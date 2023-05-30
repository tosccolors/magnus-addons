# Copyright 2021 Hunki Enterprises BV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.tools.mail import email_re, email_split


# Those are defined in odoo.tools.* in v12
def email_escape_char(email_address):
    """ Escape problematic characters in the given email address string"""
    return email_address.replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_')


class AccountMove(models.Model):
    _inherit = "account.move"

    source_email = fields.Char(string='Source Email', track_visibility='onchange')
    vendor_bill_id = fields.Many2one('account.move', string='Vendor Bill',
        help="Auto-complete from a past bill.")

    @api.model
    def message_new(self, msg_dict, custom_values=None):
        """ Overrides mail_thread message_new(), called by the mailgateway through message_process,
            to complete values for vendor bills created by mails.
        """
        # Split `From` and `CC` email address from received email to look for related partners to subscribe on the invoice
        subscribed_emails = email_split((msg_dict.get('from') or '') + ',' + (msg_dict.get('cc') or ''))
        seen_partner_ids = [pid for pid in self._find_partner_from_emails(subscribed_emails) if pid]

        # Detection of the partner_id of the invoice:
        # 1) check if the email_from correspond to a supplier
        email_from = msg_dict.get('from') or ''
        email_from = email_escape_char(email_split(email_from)[0])
        partner_id = self._search_on_partner(email_from, extra_domain=[('supplier', '=', True)])

        is_internal = lambda p: (p.user_ids and
                                 all(p.user_ids.mapped(lambda u: u.has_group('base.group_user'))))
        # 2) otherwise, if the email sender is from odoo internal users then it is likely that the vendor sent the bill
        # by mail to the internal user who, inturn, forwarded that email to the alias to automatically generate the bill
        # on behalf of the vendor.
        if not partner_id:
            user_partner_id = self._search_on_user(email_from)
            if user_partner_id and user_partner_id in self.env.ref('base.group_user').users.mapped('partner_id').ids:
                # In this case, we will look for the vendor's email address in email's body
                email_addresses = set(email_re.findall(msg_dict.get('body')))
                if email_addresses:
                    pids_list = [self._find_partner_from_emails([email], force_create=False) for email in email_addresses]
                    partner_ids = set(pid for pids in pids_list for pid in pids if pid)
                    potential_vendors = self.env['res.partner'].browse(partner_ids).filtered(lambda x: not is_internal(x))
                    partner_id = ((potential_vendors.filtered('supplier') and potential_vendors.filtered('supplier')[0].id)
                                  or (potential_vendors and potential_vendors[0].id))
            # otherwise, there's no fallback on the partner_id found for the regular author of the mail.message as we want
            # the partner_id to stay empty

        # v10 addition, we really need a partner
        if not partner_id:
            partner_id = self._find_partner_from_emails([email_from], force_create=True)[0]

        # If the partner_id can be found, subscribe it to the bill, otherwise it's left empty to be manually filled
        if partner_id:
            seen_partner_ids.append(partner_id)

        # Find the right purchase journal based on the "TO" email address
        destination_emails = email_split((msg_dict.get('to') or '') + ',' + (msg_dict.get('cc') or ''))
        alias_names = [mail_to.split('@')[0] for mail_to in destination_emails]
        journal = self.env['account.journal'].search([
            ('type', '=', 'purchase'), ('alias_name', 'in', alias_names)
        ], limit=1)

        # Create the message and the bill.
        values = dict(custom_values or {}, partner_id=partner_id, source_email=email_from)
        if journal:
            values['journal_id'] = journal.id
            # v10 addition, support operating units
            if 'operating_unit_id' in self._fields:
                values['operating_unit_id'] = journal.operating_unit_id.id
        # Passing `type` in context so that _default_journal(...) can correctly set journal for new vendor bill
        invoice = super(AccountMove, self.with_context(type=values.get('type') or 'in_invoice')).message_new(msg_dict, values)

        # Subscribe internal users on the newly created bill
        partners = self.env['res.partner'].browse(seen_partner_ids)
        partners_to_subscribe = partners.filtered(is_internal)
        if partners_to_subscribe:
            self.browse(invoice).message_subscribe([p.id for p in partners_to_subscribe])
        return invoice

    def _search_on_user(self, email_address, extra_domain=[]):
        Users = self.env['res.users'].sudo()
        # exact, case-insensitive match
        partners = Users.search([('email', '=ilike', email_address)], limit=1).mapped('partner_id')
        if not partners:
            # if no match with addr-spec, attempt substring match within name-addr pair
            email_brackets = "<%s>" % email_address
            partners = Users.search([('email', 'ilike', email_brackets)], limit=1).mapped('partner_id')
        return partners.id

    def _search_on_partner(self, email_address, extra_domain=[]):
        Partner = self.env['res.partner'].sudo()
        # exact, case-insensitive match
        partners = Partner.search([('email', '=ilike', email_address)] + extra_domain, limit=1)
        if not partners:
            # if no match with addr-spec, attempt substring match within name-addr pair
            email_brackets = "<%s>" % email_address
            partners = Partner.search([('email', 'ilike', email_brackets)] + extra_domain, limit=1)
        return partners.id

    # Load all Vendor Bill lines
    @api.onchange('vendor_bill_id')
    def _onchange_vendor_bill(self):
        if not self.vendor_bill_id:
            return {}
        self.currency_id = self.vendor_bill_id.currency_id
        new_lines = self.env['account.move.line']
        for line in self.vendor_bill_id.invoice_line_ids:
            new_lines += new_lines.new(line.read(None, load='_classic_write')[0])
        self.invoice_line_ids += new_lines
        self.payment_term_id = self.vendor_bill_id.payment_term_id
        self.vendor_bill_id = False
        return {}

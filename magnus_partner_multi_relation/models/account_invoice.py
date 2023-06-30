# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime

class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    def _compute_member_invoice(self):
        member_invoice = self.read_group([('parent_id', 'in', self.ids)], ['parent_id'], ['parent_id'])
        res = dict((data['parent_id'][0], data['parent_id_count']) for data in member_invoice)
        for line in self:
            line.member_invoice_count = res.get(line.id, 0)

    parent_id = fields.Many2one(
        comodel_name='account.invoice',
        string="Parent Invoice",
        index=True
    )

    member_invoice_count = fields.Integer('Member Invoices', compute='_compute_member_invoice')

    @api.model
    def get_members_sharing_key(self, left_partner_id, relation_type):
        members_data = {}
        relations = self.env['res.partner.relation'].search([('left_partner_id', '=', left_partner_id.id), ('type_id', '=', relation_type)])
        total_share = sum([r.distribution_key for r in relations])
        for rel in relations:
            members_data.update({rel.right_partner_id:(rel.distribution_key/total_share)})
        return members_data

    @api.model
    def _prepare_member_invoice_line(self, line, invoice, share_key):
        invoice_line = self.env['account.invoice.line'].new({
            'invoice_id': invoice.id,
            'product_id': line.product_id.id,
            'quantity': line.quantity,
            'uom_id': line.uom_id.id,
            'discount': line.discount,
        })

        # Add analytic tags to invoice line
        invoice_line.analytic_tag_ids |= line.analytic_tag_ids

        # Get other invoice line values from product onchange
        invoice_line._onchange_product_id()
        invoice_line_vals = invoice_line._convert_to_write(invoice_line._cache)

        # Analytic Invoice invoicing period is doesn't lies in same month update with property_account_wip_id
        if line.analytic_invoice_id and line.analytic_invoice_id.month_id:
            period_date = datetime.strptime(line.analytic_invoice_id.month_id.date_start, "%Y-%m-%d").strftime('%Y-%m')
            # cur_date = datetime.now().date().strftime("%Y-%m")
            invoice_date = line.analytic_invoice_id.invoice_id.date or line.analytic_invoice_id.invoice_id.date_invoice
            inv_date = datetime.strptime(invoice_date, "%Y-%m-%d").strftime('%Y-%m')
            if inv_date != period_date:
                fpos = invoice.fiscal_position_id
                account = self.env['analytic.invoice'].get_product_wip_account(line.product_id, fpos)
                invoice_line_vals.update({
                    'account_id': account.id
                })

        invoice_line_vals.update({
            'name': line.name,
            'account_analytic_id': line.account_analytic_id.id,
            'price_unit': line.price_unit * share_key,
        })
        return invoice_line_vals


    def _prepare_member_invoice(self, partner):
        self.ensure_one()
        company_id = partner.company_id if partner.company_id else self.company_id
        journal = self.journal_id or self.env['account.journal'].search(
            [('type', '=', 'sale'),
             ('company_id', '=', company_id.id)],
            limit=1)
        if not journal:
            raise ValidationError(
                _("Please define a sale journal for the company '%s'.") %
                (company_id.name or '',))
        currency = (
            # self.pricelist_id and self.pricelist_id.currency_id or
            partner.property_product_pricelist.currency_id or
            company_id.currency_id
        )
        invoice = self.env['account.invoice'].new({
            'reference': self.number,
            'type': 'out_invoice',
            'partner_id': partner.address_get(
                ['invoice'])['invoice'],
            'currency_id': currency.id,
            'journal_id': journal.id,
            'date_invoice': self.date_invoice,
            'origin': self.name,
            'company_id': company_id.id,
            'parent_id': self.id,
            'user_id': partner.user_id.id,
        })
        # Get other invoice values from partner onchange
        invoice._onchange_partner_id()
        return invoice._convert_to_write(invoice._cache)


    def _create_member_invoice(self, partner, share_key):
        self.ensure_one()
        invoice_vals = self._prepare_member_invoice(partner)
        invoice = self.env['account.invoice'].create(invoice_vals)
        for line in self.invoice_line_ids:
            invoice_line_vals = self._prepare_member_invoice_line(line, invoice, share_key)
            self.env['account.invoice.line'].create(invoice_line_vals)
        invoice.compute_taxes()
        return invoice


    def action_invoice_open(self):
        '''
            If partner has members split invoice by distribution keys,
            & Validate same invoice without creating moves
            Otherwise, call super()
        :return:
        '''

        relation_type = self.env.ref('magnus_partner_multi_relation.rel_type_consortium').id
        members_data = self.get_members_sharing_key(self.partner_id, relation_type)
        if not members_data:
            return super(AccountInvoice, self).action_invoice_open()

        # lots of duplicate calls to action_invoice_open, so we remove those already open
        to_open_invoices = self.filtered(lambda inv: inv.state != 'open')
        if to_open_invoices.filtered(lambda inv: inv.state not in ['proforma2', 'draft']):
            raise UserError(_("Invoice must be in draft or Pro-forma state in order to validate it."))
        to_open_invoices.action_date_assign()
        res = to_open_invoices.invoice_validate()

        for invoice in to_open_invoices:
            for partner, share_key in members_data.items():
                invoice._create_member_invoice(partner, share_key)

        return res


    def action_view_member_invoice(self):
        self.ensure_one()
        action = self.env.ref('account.action_invoice_tree').read()[0]
        invoice = self.search([('parent_id', 'in', self._ids)])
        if len(invoice) > 1:
            action['domain'] = [('id', 'in', invoice.ids)]
        elif invoice:
            action['views'] = [(self.env.ref('account.invoice_form').id, 'form')]
            action['res_id'] = invoice.id
        else:
            action['domain'] = [('id', 'in', invoice.ids)]
        action['context'] = {}
        return action




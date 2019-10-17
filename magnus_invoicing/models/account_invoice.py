# -*- coding: utf-8 -*-
# Copyright 2018 Magnus ((www.magnus.nl).)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta

class AccountJournal(models.Model):
    _inherit = 'account.journal'

    type = fields.Selection(selection_add=[('wip', 'WIP')])


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    @api.one
    @api.depends('invoice_line_ids')
    def _compute_month_id(self):
        analytic_invoice_id = self.invoice_line_ids.mapped('analytic_invoice_id')
        self.month_id = analytic_invoice_id and analytic_invoice_id[0].month_id.id or False

    target_invoice_amount = fields.Monetary(
        'Target Invoice Amount'
    )
    month_id = fields.Many2one(
        'date.range',
        compute='_compute_month_id',
        string="Invoicing Period"
    )
    wip_move_id = fields.Many2one(
        'account.move',
        string='WIP Journal Entry',
        readonly=True,
        index=True,
        ondelete='restrict',
        copy=False
    )

    def compute_target_invoice_amount(self):
        if self.amount_untaxed != self.target_invoice_amount:
            factor = self.target_invoice_amount / self.amount_untaxed
            discount = (1.0 - factor) * 100
            for line in self.invoice_line_ids:
                line.discount = discount

    def reset_target_invoice_amount(self):
        for line in self.invoice_line_ids:
            line.discount = 0.0

    @api.model
    def invoice_line_move_line_get(self):
        """Copy operating_unit_id from invoice line to move lines"""
        res = super(AccountInvoice, self).invoice_line_move_line_get()
        ailo = self.env['account.invoice.line']
        for move_line_dict in res:
            iline = ailo.browse(move_line_dict['invl_id'])
            if iline.user_id:
                move_line_dict['user_id'] = iline.user_id.id
        return res

    @api.model
    def line_get_convert(self, line, part):
        res = super(AccountInvoice, self).line_get_convert(line, part)
        res['user_id'] = line.get('user_id', False)
        return res

    def inv_line_characteristic_hashcode(self, invoice_line):
        """Overridable hashcode generation for invoice lines. Lines having the same hashcode
        will be grouped together if the journal has the 'group line' option. Of course a module
        can add fields to invoice lines that would need to be tested too before merging lines
        or not."""
        res = super(AccountInvoice, self).inv_line_characteristic_hashcode(invoice_line)
        return res + "%s" % (
            invoice_line['user_id']
        )

    @api.multi
    def _get_timesheet_by_group(self):
        self.ensure_one()
        aal_ids = []
        analytic_invoice_ids = self.invoice_line_ids.mapped('analytic_invoice_id')
        for analytic_invoice in analytic_invoice_ids:
            for grp_line in analytic_invoice.user_total_ids:
                aal_ids += grp_line.detail_ids
        userProject = {}
        for aal in aal_ids:
            project_id, user_id = aal.project_id if aal.project_id else aal.task_id.project_id , aal.user_id
            if project_id.correction_charge and project_id.specs_invoice_report:
                if (project_id, user_id) in userProject:
                    userProject[(project_id, user_id)] = userProject[(project_id, user_id)] + [aal]
                else:
                    userProject[(project_id, user_id)] = [aal]
        return userProject


    @api.multi
    def action_invoice_open(self):
        res = super(AccountInvoice, self).action_invoice_open()
        if self.type in ('out_invoice'):
            analytic_invoice_id = self.invoice_line_ids.mapped('analytic_invoice_id')
            # if invoicing period doesn't lie in same month
            period_date = datetime.strptime(analytic_invoice_id.month_id.date_start, "%Y-%m-%d").strftime('%Y-%m')
            cur_date = datetime.now().date().strftime("%Y-%m")
            invoice_date = self.date or self.date_invoice
            inv_date = datetime.strptime(invoice_date, "%Y-%m-%d").strftime('%Y-%m') if invoice_date else cur_date
            if inv_date != period_date and self.move_id:
                self.action_wip_move_create()
        return res

    @api.model
    def get_wip_default_account(self):
        if self.type in ('out_invoice', 'in_refund'):
            return self.journal_id.default_credit_account_id.id
        return self.journal_id.default_debit_account_id.id

    @api.model
    def invoice_line_wip_move_line_get(self):
        res = []
        for line in self.invoice_line_ids:
            if line.quantity == 0:
                continue
            tax_ids = []
            for tax in line.invoice_line_tax_ids:
                tax_ids.append((4, tax.id, None))
                for child in tax.children_tax_ids:
                    if child.type_tax_use != 'none':
                        tax_ids.append((4, child.id, None))
            analytic_tag_ids = [(4, analytic_tag.id, None) for analytic_tag in line.analytic_tag_ids]
            fpos = self.fiscal_position_id
            account = self.env['analytic.invoice'].get_product_wip_account(line.product_id, fpos)

            move_line_dict = {
                'type': 'src',
                'name': line.name.split('\n')[0][:64],
                'price_unit': line.price_unit,
                'quantity': line.quantity,
                'price': line.price_subtotal,
                'account_id': account.id,
                'product_id': line.product_id.id,
                'uom_id': line.uom_id.id,
                'account_analytic_id': line.account_analytic_id.id,
                'tax_ids': tax_ids,
                'analytic_tag_ids': analytic_tag_ids
            }
            if line['account_analytic_id']:
                move_line_dict['analytic_line_ids'] = [(0, 0, line._get_analytic_line())]
            res.append(move_line_dict)
        return res

    @api.multi
    def action_wip_move_create(self):
        """ Creates invoice related analytics and financial move lines """
        account_move = self.env['account.move']

        for inv in self:
            wip_journal = self.env.ref('magnus_invoicing.wip_journal')
            if not wip_journal.sequence_id:
                raise UserError(_('Please define sequence on the type WIP journal.'))

            if inv.wip_move_id:
                continue

            ctx = dict(self._context, lang=inv.partner_id.lang)

            if not inv.date_invoice:
                inv.with_context(ctx).write({'date_invoice': fields.Date.context_today(self)})
            company_currency = inv.company_id.currency_id

            # create move lines (one per invoice line + eventual taxes and analytic lines)
            iml = inv.invoice_line_wip_move_line_get()
            iml += inv.tax_line_move_line_get()

            diff_currency = inv.currency_id != company_currency
            # create one move line for the total and possibly adjust the other lines amount
            total, total_currency, iml = inv.with_context(ctx).compute_invoice_totals(company_currency, iml)

            name = inv.name or '/'
            date_end = self.month_id.date_end

            if inv.payment_term_id:
                totlines = inv.with_context(ctx).payment_term_id.with_context(currency_id=company_currency.id).compute(total, inv.date_invoice)[0]
                res_amount_currency = total_currency

                ctx['date'] = date_end

                for i, t in enumerate(totlines):
                    if inv.currency_id != company_currency:
                        amount_currency = company_currency.with_context(ctx).compute(t[1], inv.currency_id)
                    else:
                        amount_currency = False

                    # last line: add the diff
                    res_amount_currency -= amount_currency or 0
                    if i + 1 == len(totlines):
                        amount_currency += res_amount_currency

                    iml.append({
                        'type': 'dest',
                        'name': name,
                        'price': t[1],
                        'account_id': self.get_wip_default_account(),
                        'date_maturity': t[0],
                        'amount_currency': diff_currency and amount_currency,
                        'currency_id': diff_currency and inv.currency_id.id,
                    })
            else:
                iml.append({
                    'type': 'dest',
                    'name': name,
                    'price': total,
                    'account_id': self.get_wip_default_account(),
                    'date_maturity': inv.date_due,
                    'amount_currency': diff_currency and total_currency,
                    'currency_id': diff_currency and inv.currency_id.id,
                })
            part = self.env['res.partner']._find_accounting_partner(inv.partner_id)
            line = [(0, 0, self.line_get_convert(l, part.id)) for l in iml]
            line = inv.group_lines(iml, line)

            # journal = inv.journal_id.with_context(ctx)
            # line = inv.finalize_invoice_move_lines(line)

            sequence = wip_journal.sequence_id
            if self.type in ['in_refund'] and wip_journal.refund_sequence:
                if not wip_journal.refund_sequence_id:
                    raise UserError(_('Please define a sequence for the refunds'))
                sequence = wip_journal.refund_sequence_id
            new_name = sequence.with_context(ir_sequence_date=date_end).next_by_id()

            move_vals = {
                'ref': 'WIP Invoicing Posting',
                'line_ids': line,
                'journal_id': wip_journal.id,
                'date': date_end,
                'narration': 'WIP Invoicing Posting',
                'name':new_name,
                'to_be_reversed': True,
            }
            ctx['company_id'] = inv.company_id.id
            ctx['invoice'] = inv
            ctx_nolang = ctx.copy()
            ctx_nolang.pop('lang', None)

            wip_move = account_move.with_context(ctx_nolang).create(move_vals)

            wip_move.post()
            # make the invoice point to that wip move
            vals = {
                'wip_move_id': wip_move.id,
            }
            inv.with_context(ctx).write(vals)

            #wip reverse posting
            reverse_date = datetime.strptime(wip_move.date, "%Y-%m-%d") + timedelta(days=1)
            reverse_wip_move = wip_move.create_reversals(
                date=reverse_date, journal=wip_journal,
                move_prefix='WIP Invoicing Reverse', line_prefix='WIP Invoicing Reverse',
                reconcile=False)

            if len(reverse_wip_move) == 1:
                wip_nxt_seq = sequence.with_context(ir_sequence_date=reverse_wip_move.date).next_by_id()
                reverse_wip_move.write({'name':wip_nxt_seq})

        return True

    @api.multi
    def action_cancel(self):
        res = super(AccountInvoice, self).action_cancel()
        wip_moves = self.env['account.move']
        for inv in self:
            if inv.wip_move_id:
                wip_moves += inv.move_id

        # First, set the invoices as cancelled and detach the move ids
        self.write({'wip_move_id': False})
        if wip_moves:
            # second, invalidate the move(s)
            wip_moves.button_cancel()
            # delete the move this invoice was pointing to
            # Note that the corresponding move_lines and move_reconciles
            # will be automatically deleted too
            wip_moves.unlink()
        return res



class AccountInvoiceLine(models.Model):
    _inherit = "account.invoice.line"

    analytic_invoice_id = fields.Many2one(
        'analytic.invoice',
        string='Invoice Reference',
        ondelete='cascade',
        index=True
    )
    user_id = fields.Many2one(
        'res.users',
        'Timesheet User',
        index = True
    )
    user_task_total_line_id = fields.Many2one(
        'analytic.user.total',
        string='Grouped Analytic line',
        ondelete='cascade',
        index=True
    )

    @api.depends('account_analytic_id', 'user_id', 'invoice_id.operating_unit_id')
    @api.multi
    def _compute_operating_unit(self):
        super(AccountInvoiceLine, self)._compute_operating_unit()
        for line in self.filtered('user_id'):
            line.operating_unit_id = line.user_id._get_operating_unit_id()

    @api.multi
    def write(self, vals):
        res = super(AccountInvoiceLine, self).write(vals)
        self.filtered('analytic_invoice_id').mapped('invoice_id').compute_taxes()
        return res

    @api.model
    def default_get(self, fields):
        res = super(AccountInvoiceLine, self).default_get(fields)
        ctx = self.env.context.copy()
        if 'default_invoice_id' in ctx:
            invoice_obj = self.env['account.invoice'].browse(ctx['default_invoice_id'])
            analytic_invoice_id = invoice_obj.invoice_line_ids.mapped('analytic_invoice_id')
            if analytic_invoice_id:
                res['analytic_invoice_id'] = analytic_invoice_id.id
        return res

#    @api.onchange('product_id')
#    def _onchange_product_id(self):
#        if self.analytic_invoice_id:
#            self.invoice_id = self.env['account.invoice'].browse(self.analytic_invoice_id.invoice_ids.id)
#        return super(AccountInvoiceLine, self)._onchange_product_id()



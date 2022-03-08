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
        try:
            if self.amount_untaxed != self.target_invoice_amount:
                self.reset_target_invoice_amount()
                factor = self.target_invoice_amount / self.amount_untaxed
                discount = (1.0 - factor) * 100
                for line in self.invoice_line_ids:
                    line.discount = discount
                taxes_grouped = self.get_taxes_values()
                tax_lines = self.tax_line_ids.filtered('manual')
                for tax in taxes_grouped.values():
                    tax_lines += tax_lines.new(tax)
                self.tax_line_ids = tax_lines
        except ZeroDivisionError:
            raise UserError(_('You cannot set a target amount if the invoice line amount is 0'))


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
        if self.type and self.type in ('out_invoice'):
            analytic_invoice_id = self.invoice_line_ids.mapped('analytic_invoice_id')
            if not analytic_invoice_id:
                return res
            # if invoicing period doesn't lie in same month
            period_date = analytic_invoice_id.month_id.date_start.strftime('%Y-%m')
            cur_date = datetime.now().date().strftime("%Y-%m")
            invoice_date = self.date or self.date_invoice
            inv_date = invoice_date.strftime('%Y-%m') if invoice_date else cur_date
            if inv_date != period_date and self.move_id:
                self.action_wip_move_create()
            #if analytic invoice move_line_id then update account_analytic_line_ids field for model account.analytic.line
            if self.move_id:
                val=[self.move_id.id,self.wip_move_id.id,self.wip_move_id.reverse_entry_id.id]
                # val=[self.move_id.id,self.wip_move_id.id,self.wip_move_id.reversal_id.id]
                for move_id in val:
                    move_line = self.env['account.move.line'].search([('move_id', '=', move_id)])
                    for inv_analytic_line in self.invoice_line_ids:
                        for analytic_inv_line in inv_analytic_line.user_task_total_line_id.detail_ids:
                            analytic_line = self.env['account.analytic.line'].sudo().search(
                                [('id', '=', analytic_inv_line.id)])
                            for mov_line_id in move_line:
                                if (mov_line_id.id != False):
                                    analytic_line.account_analy_line_ids = [(4, mov_line_id.id)]
        return res

    @api.model
    def get_wip_default_account(self):
        if self.type in ('out_invoice', 'in_refund'):
            return self.journal_id.default_credit_account_id.id
        return self.journal_id.default_debit_account_id.id

    @api.multi
    def action_wip_move_create(self):
        """ Creates invoice related analytics and financial move lines """
        for inv in self:
            wip_journal = self.env.ref('magnus_timesheet.wip_journal')
            if not wip_journal.sequence_id:
                raise UserError(_('Please define sequence on the type WIP journal.'))
            sequence = wip_journal.sequence_id
            if inv.type in ['out_refund', 'in_invoice','in_refund'] or inv.wip_move_id:
                continue
            date_end = inv.month_id.date_end
            new_name = sequence.with_context(ir_sequence_date=date_end).next_by_id()
            if inv.move_id:
                wip_move = inv.move_id.wip_move_create( wip_journal, new_name, inv.account_id.id, inv.number)
            wip_move.post()
            # make the invoice point to that wip move
            inv.wip_move_id = wip_move.id
            #wip reverse posting
            reverse_date = datetime.strptime(str(wip_move.date), "%Y-%m-%d") + timedelta(days=1)
            ##########updated reversal code####
            # line_amt = sum(ml.credit + ml.debit for ml in wip_move.line_ids)
            # reconcile = False
            # if line_amt > 0:
            #     reconcile = True
            # reverse_wip_move = wip_move.create_reversals(
            #     date=reverse_date,
            #     journal=wip_journal,
            #     move_prefix='WIP Invoicing Reverse',
            #     line_prefix='WIP Invoicing Reverse',
            #     reconcile=reconcile
            # )
            ########################################
            reverse_wip_ids = wip_move.reverse_moves(date=reverse_date, journal_id=wip_journal, auto=False)
            if len(reverse_wip_ids) == 1:
                reverse_wip_move = wip_move.browse(reverse_wip_ids)
                wip_nxt_seq = sequence.with_context(ir_sequence_date=reverse_wip_move.date).next_by_id()
                reverse_wip_move.write({'name':wip_nxt_seq})
        return True

    @api.multi
    def action_cancel(self):
        res = super(AccountInvoice, self).action_cancel()
        wip_moves = self.env['account.move']
        for inv in self:
            if inv.wip_move_id:
                wip_moves += inv.wip_move_id

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

    # @api.multi
    # def write(self, vals):
    #     res = super(AccountInvoiceLine, self).write(vals)
    #     self.filtered('analytic_invoice_id').mapped('invoice_id').compute_taxes() #Issue: Vat creation double after invoice date change
    #     return res

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



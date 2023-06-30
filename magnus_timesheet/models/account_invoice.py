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
    ic_lines = fields.Boolean(
        string='IC lines generated',
        default=False
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
        """Copy user_id and trading_partner_code from invoice line to move lines"""
        res = super(AccountInvoice, self).invoice_line_move_line_get()
        ailo = self.env['account.invoice.line']
        for move_line_dict in res:
            iline = ailo.browse(move_line_dict['invl_id'])
            if iline.user_id:
                move_line_dict['user_id'] = iline.user_id.id
            if iline.trading_partner_code:
                move_line_dict['trading_partner_code'] = iline.trading_partner_code
        return res

    @api.model
    def line_get_convert(self, line, part):
        res = super(AccountInvoice, self).line_get_convert(line, part)
        res['user_id'] = line.get('user_id', False)
        res['trading_partner_code'] = line.get('trading_partner_code', False)
        if self.partner_id.trading_partner_code \
                and self.operating_unit_id.partner_id.trading_partner_code \
                and line.get('type', False) == 'dest':
            res['trading_partner_code'] = self.partner_id.trading_partner_code
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


    
    def action_invoice_open(self):
        to_process_invoices = self.filtered(lambda inv: inv.type in ('out_invoice', 'out_refund'))
        supplier_invoices = self - to_process_invoices
        if to_process_invoices:
            to_process_invoices.action_create_ic_lines()
        if supplier_invoices:
            supplier_invoices.fill_trading_partner_code_supplier_invoice()
        res = super(AccountInvoice, self).action_invoice_open()
        for invoice in to_process_invoices:
            analytic_invoice_id = invoice.invoice_line_ids.mapped('analytic_invoice_id')
            if analytic_invoice_id and invoice.type != 'out_refund':
                # if invoicing period doesn't lie in same month
                period_date = datetime.strptime(str(analytic_invoice_id.month_id.date_start), "%Y-%m-%d").strftime('%Y-%m')
                cur_date = datetime.now().date().strftime("%Y-%m")
                invoice_date = invoice.date or invoice.date_invoice
                inv_date = datetime.strptime(str(invoice_date), "%Y-%m-%d").strftime('%Y-%m') if invoice_date else cur_date
                if inv_date != period_date and invoice.move_id:
                    invoice.action_wip_move_create()
        return res

    
    def action_create_ic_lines(self):
        mapping_tp = self.env['inter.ou.account.mapping']._get_mapping_dict(self.company_id, trading_partners=True, maptype='inter_to_regular')
        mapping_notp = self.env['inter.ou.account.mapping']._get_mapping_dict(self.company_id, trading_partners=False, maptype='inter_to_regular')
        mapping2_tp = self.env['inter.ou.account.mapping']._get_mapping_dict(self.company_id, trading_partners=True, maptype='inter_to_cost')
        mapping2_notp = self.env['inter.ou.account.mapping']._get_mapping_dict(self.company_id, trading_partners=False, maptype='inter_to_cost')
        for invoice in self:
            if invoice.ic_lines:
                continue
            all_lines = invoice.invoice_line_ids
            timesheet_user = all_lines.mapped('user_id')
            ou_trading_partner = invoice.operating_unit_id.partner_id.trading_partner_code
            if not timesheet_user and ou_trading_partner:
                all_lines.write({'revenue_line':True,
                                 'trading_partner_code': invoice.partner_id.trading_partner_code or
                                                         invoice.partner_id.parent_id.trading_partner_code})
            elif not timesheet_user:
                all_lines.write({'revenue_line': True})
                continue
            intercompany_revenue_lines = invoice.invoice_line_ids.filtered(
                lambda l: l.operating_unit_id != invoice.operating_unit_id and
                          l.account_id.user_type_id in (
                              self.env.ref('account.data_account_type_other_income'),
                              self.env.ref('account.data_account_type_revenue')))
            regular_lines = all_lines - intercompany_revenue_lines if intercompany_revenue_lines else all_lines
            regular_lines.write({'revenue_line': True,
                                 'trading_partner_code': invoice.partner_id.trading_partner_code or
                                                         invoice.partner_id.parent_id.trading_partner_code
                                 if ou_trading_partner else False})
            if intercompany_revenue_lines:
                invoice_tpc = invoice.operating_unit_id.partner_id.trading_partner_code
                for line in intercompany_revenue_lines:
                    line_tpc = line.operating_unit_id.partner_id.trading_partner_code
                    trading_partners = invoice_tpc and line_tpc and invoice_tpc != line_tpc
                    if trading_partners:
                        mapping = mapping_tp
                        mapping2 = mapping2_tp
                    else:
                        mapping = mapping_notp
                        mapping2 = mapping2_notp
                    if line.account_id.id in mapping and line.account_id.id in mapping2:
                        ## revenue line
                        revenue_line = line.copy({
                            'account_id': mapping[line.account_id.id],
                            'operating_unit_id': invoice.operating_unit_id.id,
                            'user_id': False,
                            'name': line.user_id.firstname + " " + line.user_id.lastname + " " + line.name,
                            'ic_line': True,
                            'revenue_line': True,
                            'trading_partner_code': invoice.partner_id.trading_partner_code or
                                                    invoice.partner_id.parent_id.trading_partner_code
                                                        if ou_trading_partner else False})
                        revenue_line.price_unit = line.price_unit if not line.user_task_total_line_id else \
                            line.user_task_total_line_id.fee_rate
                        ## intercompany cost of sales line
                        cost_line = line.copy({
                            'account_id': mapping2[line.account_id.id],
                            'product_id': False,
                            'operating_unit_id': invoice.operating_unit_id.id,
                            'price_unit': - line.price_unit,
                            'user_id': False,
                            'name': line.user_id.firstname + " " + line.user_id.lastname + " " + line.name,
                            'ic_line': True,
                            'trading_partner_code': line_tpc if trading_partners else False
                        })
                        cost_line.invoice_line_tax_ids = [(6, 0, [])]
                        line.invoice_line_tax_ids = [(6, 0, [])]
                        line.trading_partner_code = invoice_tpc if trading_partners else False
                    else:
                        raise UserError(
                            _('The mapping from account "%s" does not exist or is incomplete.') % (
                                line.account_id.name))
                invoice.ic_lines = True
            if any(line.invoice_line_tax_ids for line in invoice.invoice_line_ids):
                invoice.compute_taxes()

    
    def action_delete_ic_lines(self):
        for invoice in self.filtered('ic_lines'):
            invoice.invoice_line_ids.filtered('ic_line').unlink()
            for line in invoice.invoice_line_ids:
                price_unit = line.price_unit
                line._set_taxes()
                line.price_unit = price_unit
                # if any(line.invoice_line_tax_ids for line in invoice.invoice_line_ids):
                invoice.compute_taxes()
            invoice.ic_lines = False

    
    def fill_trading_partner_code_supplier_invoice(self):
        for invoice in self:
            if not (invoice.partner_id.trading_partner_code or invoice.partner_id.parent_id.trading_partner_code):
                intercompany_lines = invoice.invoice_line_ids.filtered(
                    lambda l: l.operating_unit_id != invoice.operating_unit_id)
                if intercompany_lines:
                    invoice_tpc = invoice.operating_unit_id.partner_id.trading_partner_code
                    for line in intercompany_lines:
                        line_tpc = line.operating_unit_id.partner_id.trading_partner_code
                        trading_partners = invoice_tpc and line_tpc and invoice_tpc != line_tpc
                        line.trading_partner_code = invoice_tpc if trading_partners else False
            elif invoice.operating_unit_id.partner_id.trading_partner_code:
                invoice.invoice_line_ids.write({'trading_partner_code': invoice.partner_id.trading_partner_code  or
                                                         invoice.partner_id.parent_id.trading_partner_code})

    def set_move_to_draft(self):
        if self.move_id.state == 'posted':
            if not self.move_id.journal_id.update_posted:
                raise UserError(_('Please allow to cancel entries from this journal.'))
            self.move_id.state = 'draft'
            return 'posted'
        return 'draft'

    @api.model
    def get_wip_default_account(self):
        if self.type in ('out_invoice', 'in_refund'):
            return self.journal_id.default_credit_account_id.id
        return self.journal_id.default_debit_account_id.id

    
    def action_wip_move_create(self):
        """ Creates invoice related analytics and financial move lines """
        for inv in self:
            # wip_journal = self.env.ref('magnus_timesheet.wip_journal')
            # if not wip_journal.sequence_id:
            #     raise UserError(_('Please define sequence on the type WIP journal.'))
            if not inv.company_id.wip_journal_id:
                raise UserError(_('Please define WIP journal on company.'))
            if not inv.company_id.wip_journal_id.sequence_id:
                raise UserError(_('Please define sequence on the type WIP journal.'))
            wip_journal = inv.company_id.wip_journal_id
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
    trading_partner_code = fields.Char(
        'Trading Partner Code',
        help="Specify code of Trading Partner"
    )
    user_task_total_line_id = fields.Many2one(
        'analytic.user.total',
        string='Grouped Analytic line',
        ondelete='cascade',
        index=True
    )
    ic_line = fields.Boolean(
        string='IC line',
        default=False
    )
    revenue_line = fields.Boolean(
        string='Revenue line',
        default=False
    )

    @api.depends('account_analytic_id', 'user_id', 'invoice_id.operating_unit_id')
    
    def _compute_operating_unit(self):
        super(AccountInvoiceLine, self)._compute_operating_unit()
        for line in self.filtered('user_id'):
            line.operating_unit_id = line.user_id._get_operating_unit_id()

    
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

    @api.onchange('user_task_total_line_id.fee_rate')
    def _onchange_fee_rate(self):
        if self.user_task_total_line_id.fee_rate:
            self.price_unit = self.user_task_total_line_id.fee_rate

    @api.onchange('product_id')
    def _onchange_product_id(self):
        res = super(AccountInvoiceLine, self)._onchange_product_id()
        if self.invoice_id.type in 'out_invoice' \
                and self.operating_unit_id != self.invoice_id.operating_unit_id \
                and self.account_id.user_type_id in (
                                            self.env.ref('account.data_account_type_other_income'),
                                            self.env.ref('account.data_account_type_revenue')
                                            ):
           account = self.account_id
           trading_partners = self.operating_unit_id.partner_id.trading_partner_code \
                              and self.invoice_id.operating_unit_id.partner_id.trading_partner_code
           self.account_id = self.env['inter.ou.account.mapping']._get_mapping_dict(
                                                                self.company_id, trading_partners,'product_to_inter'
                                                                )[account.id]
        return res

#    @api.onchange('product_id')
#    def _onchange_product_id(self):
#        if self.analytic_invoice_id:
#            self.invoice_id = self.env['account.invoice'].browse(self.analytic_invoice_id.invoice_ids.id)
#        return super(AccountInvoiceLine, self)._onchange_product_id()



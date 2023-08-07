# -*- coding: utf-8 -*-
# © 2016-17 Eficent Business and IT Consulting Services S.L.
# © 2016 Serpent Consulting Services Pvt. Ltd.
# © 2018 Magnus Group B.V.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).
from odoo.tools.translate import _
from odoo import api, fields, models
from odoo.exceptions import UserError
from datetime import datetime, timedelta

class AccountMoveLine(models.Model):
    _inherit = "account.move.line"


    @api.depends('full_reconcile_id','invoice_line_id','invoice_id')
    def _compute_trading_partner_code(self):
        invoice_lines = self.filtered('invoice_line_id')
        ar_ap_lines = self.filtered(lambda line:
                                (line.invoice_id.partner_id.trading_partner_code or
                                 line.invoice_id.partner_id.parent_id.trading_partner_code) and
                                line.invoice_id.operating_unit_id.partner_id.trading_partner_code and
                                line.account_id.internal_type in ('receivable', 'payable'))
        reconciled_arap_lines = ar_ap_lines.filtered('full_reconcile_id')
        fr_ids = reconciled_arap_lines.mapped('full_reconcile_id')
        reconciled_payment_lines = self.filtered(lambda line: line.full_reconcile_id in fr_ids) - ar_ap_lines
        for il in invoice_lines:
            il.trading_partner_code = il.invoice_line_id.trading_partner_code
        for aal in ar_ap_lines:
            aal.trading_partner_code = aal.invoice_id.partner_id.trading_partner_code or \
                                       aal.invoice_id.partner_id.parent_id.trading_partner_code
        for pl in reconciled_payment_lines:
            pl.trading_partner_code = self.search([
                ('full_reconcile_id','=', pl.full_reconcile_id.id),
                ('invoice_id' ,'!=', False)
                 ])[0].trading_partner_code



    user_id = fields.Many2one(
        'res.users',
        string='Timesheet User'
    )
    trading_partner_code = fields.Char(
        'Trading Partner Code',
        compute=_compute_trading_partner_code,
        # inverse=_inverse_trading_partner_code,
        store= True,
        help="Specify code of Trading Partner"
    )
    invoice_line_id = fields.Many2one(
        'account.invoice.line',
        string='Originating Invoice Line'
    )

    @api.multi
    @api.constrains('operating_unit_id', 'analytic_account_id','user_id')
    def _check_analytic_operating_unit(self):
        for rec in self.filtered('user_id'):
            if not rec.operating_unit_id == \
                                    rec.user_id._get_operating_unit_id():
                raise UserError(_('The Operating Unit in the'
                                  ' Move Line must be the '
                                  'Operating Unit in the department'
                                  ' of the user/employee'))
        super(AccountMoveLine, self - self.filtered('user_id'))._check_analytic_operating_unit()

    @api.onchange('analytic_account_id', 'user_id')
    @api.multi
    def onchange_operating_unit(self):
        super(AccountMoveLine, self).onchange_operating_unit()
        if self.user_id:
            self.operating_unit_id = \
                self.user_id._get_operating_unit_id()

class AccountMove(models.Model):
    _inherit = "account.move"

    # override post(), when first post, nothing extra. When move.name exists,
    # it cannot be first posting. Then 'OU-balancing' lines are unlinked.
    @api.multi
    def post(self):
        for move in self:
            if not move.company_id.ou_is_self_balanced or not move.name:
                continue
            for line in move.line_ids:
                if line.name == 'OU-Balancing':
                    line.with_context(wip=True).unlink()
        res = super(AccountMove, self).post()
        return res

    @api.multi
    def wip_move_create(self, wip_journal, name, ar_account_id, ref=None):
        self.ensure_one()
        move_date = datetime.strptime(self.date, "%Y-%m-%d")
        last_day_month_before = (move_date - timedelta(days=move_date.day)).strftime("%Y-%m-%d")
        default = {
            'name': name,
            'ref':  ref if ref else 'WIP Invoicing Posting',
            'journal_id': wip_journal.id,
            'date': last_day_month_before,
            'narration': 'WIP Invoicing Posting',
            'to_be_reversed': True,
        }
        wip_move = self.copy(default)
        mls = wip_move.line_ids
        ## we filter all BS lines out of all move lines. And also all "null" lines because of reconcile problem
        # All filtered out lines are unlinked. All will be kept unchanged and copied with reversing debit/credit
        # and replace P/L account by wip-account.
        ids = []
        ids.append(self.env.ref('account.data_account_type_other_income').id)
        ids.append(self.env.ref('account.data_account_type_revenue').id)
        ids.append(self.env.ref('account.data_account_type_depreciation').id)
        ids.append(self.env.ref('account.data_account_type_expenses').id)
        ids.append(self.env.ref('account.data_account_type_direct_costs').id)
        # Balance Sheet lines
        bs_move_lines = mls.filtered(lambda r: r.account_id.user_type_id.id not in ids)
        # lines with both debit and credit equals 0
        null_lines = mls.filtered(lambda r: r.credit + r.debit == 0.0)
        # leaving only not-null Profit and Loss lines
        pl_move_lines = mls - bs_move_lines - null_lines
        bs_move_lines.unlink()
        null_lines.unlink()
        default = {
            'account_id': wip_journal.default_credit_account_id.id
        }
        for line in pl_move_lines:
            wip_line = line.copy(default)
            if line.credit != 0:
                wip_line.credit = line.debit
                wip_line.debit = line.credit
            else:
                wip_line.debit = line.credit
                wip_line.credit = line.debit
        return wip_move


class InteroOUAccountMapping(models.Model):
    _name = 'inter.ou.account.mapping'
    _description = 'Inter Operating Unit Account Mapping'
    _rec_name = 'account_id'

    @api.model
    def _get_revenue_account_domain(self):
        ids = [self.env.ref('account.data_account_type_other_income').id,
               self.env.ref('account.data_account_type_revenue').id]
        return [('deprecated', '=', False), ('user_type_id', 'in', ids)]

    @api.model
    def _get_cost_of_sales_account_domain(self):
        ids = [self.env.ref('account.data_account_type_direct_costs').id]
        return [('deprecated', '=', False), ('user_type_id', 'in', ids)]

    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        default=lambda self: self.env['res.company']._company_default_get(
            'inter.ou.account.mapping')
    )
    account_id = fields.Many2one(
        'account.account',
        string='Product Revenue Account',
        domain=_get_revenue_account_domain,
        required=True
    )
    inter_ou_account_id = fields.Many2one(
        'account.account',
        string='Inter OU Account',
        domain=_get_revenue_account_domain,
        required=True
    )
    revenue_account_id = fields.Many2one(
        'account.account',
        string='Revenue Account',
        domain=_get_revenue_account_domain,
        required=True
    )
    cost_account_id = fields.Many2one(
        'account.account',
        string='Inter OU Cost of Sales Account',
        domain=_get_cost_of_sales_account_domain,
        required=True
    )
    trading_partners = fields.Boolean(
        string='both operating_units are trading partners',
        default=False
    )

    @api.model
    def _get_mapping_dict(self, company_id, trading_partners, maptype):
        """return a dict with:
        key = ID of account,
        value = ID of mapped_account"""
        mappings = self.search([
            ('company_id', '=', company_id.id),('trading_partners','=', trading_partners)])
        mapping = {}
        if maptype == 'product_to_inter':
            for item in mappings:
                mapping[item.account_id.id] = item.inter_ou_account_id.id
        if maptype == 'inter_to_regular':
            for item in mappings:
                mapping[item.inter_ou_account_id.id] = item.revenue_account_id.id
        if maptype == 'regular_to_cost':
            for item in mappings:
                mapping[item.revenue_account_id.id] = item.cost_account_id.id
        if maptype == 'inter_to_cost':
            for item in mappings:
                mapping[item.inter_ou_account_id.id] = item.cost_account_id.id
        return mapping
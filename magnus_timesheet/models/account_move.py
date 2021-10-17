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

    user_id = fields.Many2one(
        'res.users',
        string='Timesheet User'
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
    def add_invoiced_revenue_to_move(self, intercompany_revenue_lines, operating_unit_id):
        self.ensure_one()
        mapping = self.env['inter.ou.account.mapping']._get_mapping_dict(self.company_id, 'inter_to_regular')
        mapping2 = self.env['inter.ou.account.mapping']._get_mapping_dict(self.company_id, 'inter_to_cost')
        for line in intercompany_revenue_lines:
            if line.account_id.id in mapping and line.account_id.id in mapping2:
                ## revenue_line
                line.with_context(wip=True).copy({
                        'account_id': mapping[line.account_id.id],
                        'operating_unit_id': operating_unit_id,
                        'user_id': False,
                        'name': line.user_id.firstname + " " + line.user_id.lastname + " " + line.name
                })
                ## cost_line =
                line.with_context(wip=True).copy({
                        'account_id': mapping2[line.account_id.id],
                        'operating_unit_id': operating_unit_id,
                        'debit': line.credit,
                        'credit': line.debit,
                        'user_id': False,
                        'name': line.user_id.firstname + " " + line.user_id.lastname + " " + line.name
                })
            else:
                raise UserError(_('The mapping from account "%s" does not exist or is incomplete.') % (line.account_id.name))


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
    def _get_revenuw_account_domain(self):
        ids = [self.env.ref('account.data_account_type_other_income').id,
               self.env.ref('account.data_account_type_revenue').id]
        return [('deprecated', '=', False), ('user_type_id', 'in', ids)]

    @api.model
    def _get_cost_of_sales_account_domain(self):
        ids = [self.env.ref('account.data_account_type_direct_costs').id]
        return [('deprecated', '=', False), ('user_type_id', 'in', ids)]

    company_id = fields.Many2one(
        'res.company', string='Company', required=True,
        default=lambda self: self.env['res.company']._company_default_get(
            'inter.ou.account.mapping'))
    account_id = fields.Many2one(
        'account.account', string='Regular Revenue Account',
        domain=_get_revenuw_account_domain,
        required=True)
    inter_ou_account_id = fields.Many2one(
        'account.account', string='Inter OU Account',
        domain=_get_revenuw_account_domain,
        required=True)
    cost_account_id = fields.Many2one(
        'account.account', string='Intercompany Cost of Sales Account',
        domain=_get_cost_of_sales_account_domain,
        required=True)

    @api.model
    def _get_mapping_dict(self, company_id, maptype):
        """return a dict with:
        key = ID of account,
        value = ID of mapped_account"""
        mappings = self.search([
            ('company_id', '=', company_id.id)])
        mapping = {}
        if maptype == 'regular_to_inter':
            for item in mappings:
                mapping[item.account_id.id] = item.inter_ou_account_id.id
        if maptype == 'inter_to_regular':
            for item in mappings:
                mapping[item.inter_ou_account_id.id] = item.account_id.id
        if maptype == 'regular_to_cost':
            for item in mappings:
                mapping[item.account_id.id] = item.cost_account_id.id
        if maptype == 'inter_to_cost':
            for item in mappings:
                mapping[item.inter_ou_account_id.id] = item.cost_account_id.id
        return mapping
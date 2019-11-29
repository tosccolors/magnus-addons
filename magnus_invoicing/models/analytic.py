# -*- coding: utf-8 -*-
# Copyright 2018 Magnus ((www.magnus.nl).)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _
from datetime import datetime, timedelta
from odoo.exceptions import UserError, ValidationError
import calendar

class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    @api.one
#    @api.depends('month_of_last_wip')
    def _compute_month_id(self):
        if self.month_of_last_wip:
            date_end = self.env['date.range'].browse(month_of_last_wip).date_end
            first_of_next_month_date = (datetime.strptime(date_end, "%Y-%m-%d") + timedelta(days=1)).strftime(
                "%Y-%m-%d")
            self.wip_month_id = self.find_daterange_month(first_of_next_month_date)
        else self.wip_month_id = self.month_id

    state = fields.Selection([
        ('draft', 'Draft'),
        ('open', 'Confirmed'),
        ('delayed', 'Delayed'),
        ('invoiceable', 'To be Invoiced'),
        ('progress', 'In Progress'),
        ('invoice_created', 'Invoice Created'),
        ('invoiced', 'Invoiced'),
        ('write-off', 'Write-Off'),
        ('change-chargecode', 'Change-Chargecode'),
        ('re_confirmed', 'Re-Confirmed'),
    ],
        string='Status',
        readonly=True,
        copy=False,
        index=True,
        track_visibility='onchange',
        default='draft'
    )
    user_total_id = fields.Many2one(
        'analytic.user.total',
        string='Summary Reference',
        index=True
    )
    date_of_last_wip = fields.Date("Date Of Last WIP")
    wip_month_id = fields.Many2one('date.range',
        compute='_compute_month_id',
        string="Month of Analytic Line or last Wip Posting")
    date_of_next_reconfirmation = fields.Date("Date Of Next Reconfirmation")
    month_of_last_wip = fields.Many2one("date.range", "Month Of Next Reconfirmation")

    @api.multi
    def write(self, vals):
        #Condition to check if sheet_id already exists!
        if 'sheet_id' in vals and vals['sheet_id'] == False and self.filtered('sheet_id'):
            raise ValidationError(_(
                'Timesheet link can not be deleted for %s.\n '
            ) % self)

        # don't call super if only state has to be updated
        if self and 'state' in vals and len(vals) == 1:
            state = vals['state']
            cond, rec = ("IN", tuple(self.ids)) if len(self) > 1 else ("=",
                       self.id)
            self.env.cr.execute("""
                               UPDATE %s SET state = '%s' WHERE id %s %s
                               """ % (self._table, state, cond, rec))
            self.env.invalidate_all()
            vals.pop('state')
            return True

        if self.filtered('ts_line') and not (
                'unit_amount' in vals or
                'product_uom_id' in vals or
                'sheet_id' in vals or
                'date' in vals or
                'project_id' in vals or
                'task_id' in vals or
                'user_id' in vals or
                'name' in vals or
                'ref' in vals):

            #always copy context to keep other context reference
            context = self.env.context.copy()
            context.update({'analytic_check_state': True})
            return super(AccountAnalyticLine, self.with_context(context)).write(
                vals)
        return super(AccountAnalyticLine, self).write(vals)

    def _check_state(self):
        """
        to check if any lines computes method calls allow to modify
        :return: True or super
        """
        context = self.env.context.copy()
        if 'analytic_check_state' in context \
                or 'active_invoice_id' in context:
            return True
        return super(AccountAnalyticLine, self)._check_state()

    @api.model
    def run_reconfirmation_process(self):
        current_date = datetime.now().date()
        # pre_month_start_date = current_date.replace(day=1, month=current_date.month - 1)
        month_days = calendar.monthrange(current_date.year, current_date.month)[1]
        month_end_date = current_date.replace(day=month_days)
        
        domain = [('date_of_next_reconfirmation', '<=', month_end_date), ('state', '=', 'delayed')]
        query_line = self._where_calc(domain)
        self_tables, where_clause, where_clause_params = query_line.get_sql()

        list_query = ("""                    
            UPDATE {0}
            SET state = 're_confirmed', date_of_next_reconfirmation = false
            WHERE {1}                          
                 """.format(
            self_tables,
            where_clause
        ))
        self.env.cr.execute(list_query, where_clause_params)
        return True
        


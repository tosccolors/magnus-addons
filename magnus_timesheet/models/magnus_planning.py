# -*- coding: utf-8 -*-

import time
from datetime import datetime
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models
from odoo.tools.translate import _
from odoo.tools.sql import drop_view_if_exists
from odoo.exceptions import UserError, ValidationError


class MagnusPlanning(models.Model):
    _name = "magnus.planning"
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    _order = "id desc"
    _description = "Planning"
    _rec_name = "user_id"

    @api.one
    @api.constrains('week_from', 'week_to')
    def _check_weeks(self):
        start_date = self.week_from.date_start
        end_date = self.week_to.date_start
        if (start_date and end_date) and (start_date > end_date):
            raise ValidationError(_("End week should be greater than start week."))


    def _default_date_from(self):
        user = self.env['res.users'].browse(self.env.uid)
        r = user.company_id and user.company_id.timesheet_range or 'month'
        if r == 'month':
            return time.strftime('%Y-%m-01')
        elif r == 'week':
            return (datetime.today() + relativedelta(weekday=0, days=-6)).strftime('%Y-%m-%d')
        elif r == 'year':
            return time.strftime('%Y-01-01')
        return fields.Date.context_today(self)

    def _default_date_to(self):
        user = self.env['res.users'].browse(self.env.uid)
        r = user.company_id and user.company_id.timesheet_range or 'month'
        if r == 'month':
            return (datetime.today() + relativedelta(months=+1, day=1, days=-1)).strftime('%Y-%m-%d')
        elif r == 'week':
            return (datetime.today() + relativedelta(weekday=6)).strftime('%Y-%m-%d')
        elif r == 'year':
            return time.strftime('%Y-12-31')
        return fields.Date.context_today(self)

    def _default_employee(self):
        emp_ids = self.env['hr.employee'].search([('user_id', '=', self.env.uid)])
        return emp_ids and emp_ids[0] or False

    employee_id = fields.Many2one('hr.employee', string='Employee', default=_default_employee, required=True)
    user_id = fields.Many2one('res.users', related='employee_id.user_id', string='User', store=True, readonly=True)
    date_from = fields.Date(string='Date From', default=_default_date_from, required=True, index=True)
    date_to = fields.Date(string='Date To', default=_default_date_to, required=True, index=True)
    planning_ids = fields.Many2many('account.analytic.line', 'magnus_planning_analytic_line_rel', 'planning_id',
                                    'analytic_line_id', string='Planning lines', copy=False)
    company_id = fields.Many2one('res.company', string='Company')
    week_from = fields.Many2one('date.range', string='week from', required=True, index=True)
    week_to = fields.Many2one('date.range', string='week to', required=True, index=True)

    @api.onchange('week_from', 'week_to')
    def onchange_week(self):
        self.date_from = self.week_from.date_start
        self.date_to = self.week_to.date_end

    def _create_planning(self):
        aal_domain = [('id', 'in', self.planning_ids.ids)]
        aal_query_line = self.planning_ids._where_calc(aal_domain)
        aal_tables, aal_where_clause, aal_where_clause_params = aal_query_line.get_sql()

        list_query = ("""
                  INSERT INTO
                       magnus_planning
                       (create_uid, create_date, write_uid, write_date, employee_id, user_id, date_from, date_to, week_from, week_to)
                    SELECT                    
                        {0} AS create_uid,
                        {1}::TIMESTAMP AS create_date,
                        {0} AS write_uid,
                        {1}::TIMESTAMP AS write_date,
                        {6}.employee_id AS employee_id,
                        {6}.user_id AS user_id,
                        {2} AS date_from,
                        {3} AS date_to,
                        {4} AS week_from,
                        {5} AS week_to
                    FROM
                       {6}
                    WHERE {7} AND {6}.employee_id NOT IN (select employee_id from magnus_planning)
                    GROUP BY {6}.employee_id, {6}.user_id 
                    """.format(
                    self._uid,
                    "'%s'" % str(fields.Datetime.to_string(fields.datetime.now())),
                    "'%s'" % str(self.week_from.date_start),
                    "'%s'" % str(self.week_to.date_end),
                    self.week_from.id,
                    self.week_to.id,
                    aal_tables,
                    aal_where_clause
                ))

        self.env.cr.execute(list_query, aal_where_clause_params)

        rel_query = ("""
                      INSERT INTO
                           magnus_planning_analytic_line_rel
                           (planning_id, analytic_line_id)
                        SELECT
                            mp.id as planning_id,
                            {0}.id as analytic_line_id
                            FROM {0}
                            JOIN magnus_planning mp
                            ON {0}.employee_id = mp.employee_id
                            WHERE {1}
                        EXCEPT
                        SELECT
                            planning_id, analytic_line_id
                            FROM magnus_planning_analytic_line_rel
                        """.format(
                    aal_tables,
                    aal_where_clause
                ))

        self.env.cr.execute(rel_query, aal_where_clause_params)


    def unlink_analytic_entries(self):
        analytic = self.planning_ids.filtered(lambda x: x.unit_amount == 0)
        analytic.unlink()
        return True

    @api.model
    def create(self ,vals):
        res = super(MagnusPlanning, self).create(vals)
        res.unlink_analytic_entries()
        res._create_planning()
        return res

    @api.multi
    def write(self, vals):
        res = super(MagnusPlanning, self).write(vals)
        self.unlink_analytic_entries()
        self._create_planning()
        return res



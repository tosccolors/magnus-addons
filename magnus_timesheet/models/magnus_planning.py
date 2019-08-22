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
        if self.week_from:
            planning = self.search_count([('employee_id', '=', self.employee_id.id),('week_from', '<=', self.week_from.id),('week_to', '>=', self.week_from.id)])
            if planning > 1:
                raise ValidationError(_("Week range already exists."))


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
    
    # def get_employee_manager_ids(self):
    #     mgr_ids = []
    #     # get department's manager list
    #     department_id = self.employee_id.department_id.id
    #     self.env.cr.execute("""
    #         WITH RECURSIVE
    #             subordinates AS(
    #                 SELECT id, parent_id, manager_id  FROM hr_department WHERE id = %s
    #                 UNION
    #                 SELECT h.id, h.parent_id, h.manager_id FROM hr_department h
    #                 INNER JOIN subordinates s ON s.parent_id = h.id)
    #             SELECT  *  FROM subordinates"""
    #             % (department_id))
    #     dept_mgr_ids = [x[2] for x in self.env.cr.fetchall()]
    #
    #     # get employee's manager list
    #     self.env.cr.execute("""
    #         WITH RECURSIVE
    #             subordinates AS(
    #                 SELECT id, parent_id  FROM hr_employee WHERE id = %s
    #                 UNION
    #                 SELECT hr.id, hr.parent_id FROM hr_employee hr
    #                 INNER JOIN subordinates s ON s.parent_id = hr.id)
    #             SELECT  *  FROM subordinates"""
    #             % (self.employee_id.id))
    #
    #     employee_mgr_ids = [x[1] for x in self.env.cr.fetchall()]
    #     mgr_ids = list(set(dept_mgr_ids+employee_mgr_ids+[self.employee_id.id]))
    #     return mgr_ids

    def get_employee_child_ids(self):
        # get department's manager list
        self.env.cr.execute("""
            WITH RECURSIVE
                subordinates AS(
                    SELECT id, parent_id, manager_id  FROM hr_department WHERE id = %s
                    UNION
                    SELECT h.id, h.parent_id, h.manager_id FROM hr_department h
                    INNER JOIN subordinates s ON s.id = h.parent_id)
                SELECT  *  FROM subordinates"""
                % (self.employee_id.department_id.id))
        dept_mgr_ids = [x[2] for x in self.env.cr.fetchall() if x[2]]

        # get employees list
        self.env.cr.execute("""
            WITH RECURSIVE
                subordinates AS(
                    SELECT id, parent_id  FROM hr_employee WHERE id = %s
                    UNION
                    SELECT hr.id, hr.parent_id FROM hr_employee hr
                    INNER JOIN subordinates s ON s.id = hr.parent_id)
                SELECT  *  FROM subordinates"""
                % (self.employee_id.id))

        employee_ids = [x[0] for x in self.env.cr.fetchall() if x[0]]
        child_ids = list(set(dept_mgr_ids+employee_ids))
        return child_ids

    def get_planning_from_managers(self):
        line_query = ("""
                        INSERT INTO
                           magnus_planning_analytic_line_rel
                           (planning_id, analytic_line_id)
                            SELECT
                                mp.id as planning_id,
                                aal.id as analytic_line_id
                            FROM 
                                account_analytic_line aal
                                JOIN magnus_planning mp ON aal.employee_id = mp.employee_id
                                JOIN magnus_planning_analytic_line_rel rel ON rel.analytic_line_id = aal.id
                                WHERE aal.week_id >= {0} AND aal.week_id <= {1}
                                AND mp.id = {2} 
                          EXCEPT
                            SELECT
                              planning_id, analytic_line_id
                              FROM magnus_planning_analytic_line_rel
                """.format(
            self.week_from.id,
            self.week_to.id,
            self.id))

        self.env.cr.execute(line_query)

    def get_planning_from_employees(self):
        child_emp_ids = self.get_employee_child_ids()
        line_query = ("""
                INSERT INTO
                   magnus_planning_analytic_line_rel
                   (planning_id, analytic_line_id)
                    SELECT 
                        {0}, aal.id 
                      FROM account_analytic_line aal 
                      WHERE 
                        aal.week_id >= {1} AND aal.week_id <= {2}
                        AND aal.id IN (
		                    SELECT analytic_line_id FROM magnus_planning_analytic_line_rel WHERE planning_id IN 
                            (SELECT id FROM magnus_planning WHERE employee_id IN {3}))
                    EXCEPT
                        SELECT
                          planning_id, analytic_line_id
                          FROM magnus_planning_analytic_line_rel
                """.format(
                    self.id,
                    self.week_from.id,
                    self.week_to.id,
                    tuple(child_emp_ids)
                    ))
        self.env.cr.execute(line_query)


    @api.one
    def _compute_planning_lines(self):
        self.planning_ids_compute = False
        if self.employee_id.user_id.has_group("hr.group_hr_user") or self.employee_id.user_id.has_group("hr.group_hr_manager"):
            self.get_planning_from_employees()
        else:
            self.get_planning_from_managers()

    @api.one
    def compute_planning_lines(self):
        self._compute_planning_lines()

    employee_id = fields.Many2one('hr.employee', string='Employee', default=_default_employee, required=True)
    user_id = fields.Many2one('res.users', related='employee_id.user_id', string='User', store=True, readonly=True)
    date_from = fields.Date(string='Date From', default=_default_date_from, required=True, index=True)
    date_to = fields.Date(string='Date To', default=_default_date_to, required=True, index=True)
    planning_ids = fields.Many2many('account.analytic.line', 'magnus_planning_analytic_line_rel', 'planning_id',
                                    'analytic_line_id', string='Planning lines', copy=False)
    company_id = fields.Many2one('res.company', string='Company')
    week_from = fields.Many2one('date.range', string='week from', required=True, index=True)
    week_to = fields.Many2one('date.range', string='week to', required=True, index=True)
    planning_ids_compute = fields.Boolean(compute='_compute_planning_lines')

    @api.onchange('week_from', 'week_to')
    def onchange_week(self):
        self.date_from = self.week_from.date_start
        self.date_to = self.week_to.date_end

    # def _create_planning(self):
    #     aal_domain = [('id', 'in', self.planning_ids.ids)]
    #     aal_query_line = self.planning_ids._where_calc(aal_domain)
    #     aal_tables, aal_where_clause, aal_where_clause_params = aal_query_line.get_sql()
    #
    #     list_query = ("""
    #               INSERT INTO
    #                    magnus_planning
    #                    (create_uid, create_date, write_uid, write_date, employee_id, user_id, date_from, date_to, week_from, week_to)
    #                 SELECT
    #                     {0} AS create_uid,
    #                     {1}::TIMESTAMP AS create_date,
    #                     {0} AS write_uid,
    #                     {1}::TIMESTAMP AS write_date,
    #                     {6}.employee_id AS employee_id,
    #                     {6}.user_id AS user_id,
    #                     {2} AS date_from,
    #                     {3} AS date_to,
    #                     {4} AS week_from,
    #                     {5} AS week_to
    #                 FROM
    #                    {6}
    #                 WHERE {7} AND
    #                     {6}.employee_id NOT IN
    #                       (SELECT employee_id FROM magnus_planning WHERE week_from <= {4} AND week_to >= {4})
    #                 GROUP BY {6}.employee_id, {6}.user_id
    #                 """.format(
    #                 self._uid,
    #                 "'%s'" % str(fields.Datetime.to_string(fields.datetime.now())),
    #                 "'%s'" % str(self.week_from.date_start),
    #                 "'%s'" % str(self.week_to.date_end),
    #                 self.week_from.id,
    #                 self.week_to.id,
    #                 aal_tables,
    #                 aal_where_clause
    #             ))
    #
    #     self.env.cr.execute(list_query, aal_where_clause_params)
    #
    #     rel_query = ("""
    #                   INSERT INTO
    #                        magnus_planning_analytic_line_rel
    #                        (planning_id, analytic_line_id)
    #                     SELECT
    #                         mp.id as planning_id,
    #                         {0}.id as analytic_line_id
    #                         FROM {0}
    #                         JOIN magnus_planning mp
    #                         ON {0}.employee_id = mp.employee_id
    #                         WHERE {1}
    #                         AND mp.week_from <= {2} AND mp.week_to >= {2}
    #                     EXCEPT
    #                     SELECT
    #                         planning_id, analytic_line_id
    #                         FROM magnus_planning_analytic_line_rel
    #                     """.format(
    #                 aal_tables,
    #                 aal_where_clause,
    #                 self.week_from.id,
    #                 self.week_to.id,
    #             ))
    #
    #     self.env.cr.execute(rel_query, aal_where_clause_params)


    # def unlink_analytic_entries(self):
    #     analytic = self.planning_ids.filtered(lambda x: x.unit_amount == 0)
    #     analytic.unlink()
    #     return True

    # @api.model
    # def create(self ,vals):
    #     res = super(MagnusPlanning, self).create(vals)
    #     res.unlink_analytic_entries()
    #     res._create_planning()
    #     return res

    # @api.multi
    # def write(self, vals):
    #     res = super(MagnusPlanning, self).write(vals)
    #     self.unlink_analytic_entries()
    #     self._create_planning()
    #     return res


class MagnusStandbyPlanning(models.Model):
    _name = "magnus.standby.planning"
    _description = "Stand-By Planning"
    _rec_name = 'employee_id'

    @api.constrains('date_from', 'date_to')
    def _check_date(self):
        for planning in self:
            domain = [
                ('date_from', '<=', planning.date_to),
                ('date_to', '>=', planning.date_from),
                ('employee_id', '=', planning.employee_id.id),
                ('id', '!=', planning.id),
            ]
            nplanning = self.search_count(domain)
            if nplanning:
                raise ValidationError(_('%s can not have 2 planning that overlaps on same day!')%(planning.employee_id.name))

    @api.model
    def default_get(self, fields):
        rec = super(MagnusStandbyPlanning, self).default_get(fields)
        emp_ids = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
        rec.update({'employee_id': emp_ids and emp_ids.id or False})
        return rec

    employee_id = fields.Many2one('hr.employee', string='Employee', required=True)
    user_id = fields.Many2one('res.users', related='employee_id.user_id', string='User', store=True, readonly=True)
    department_id = fields.Many2one('hr.department', related='employee_id.department_id', string='Department',
                                    readonly=True, store=True)
    date_from = fields.Date(string='Date From', required=True, index=True)
    date_to = fields.Date(string='Date To', required=True, index=True)
    note = fields.Text(string='Note')



# -*- coding: utf-8 -*-

import time
from datetime import datetime
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models
from odoo.tools.translate import _
from odoo.tools.sql import drop_view_if_exists
from odoo.exceptions import UserError, ValidationError

class MagnusPlanningOld(models.Model):
    _name = 'magnus.planning.old'
    _description = 'Magnus Planing'
    _rec_name = 'task_id'

    @api.model
    def _default_user(self):
        return self.env.context.get('user_id', self.env.user.id)

    def _default_analytic_ids(self):
        # your list of project should come from the context, some selection
        # in a previous wizard or wherever else
        projects = self.env['project.project'].browse([1, 2, 3])
        # same with users
        users = self.env['res.users'].browse([1, 2, 3])
        return [
            (0, 0, {
                'project_id': p.id,
                'user_id': u.id,
                'unit_amount': 0,
                'message_needaction': False,
                'date_deadline': fields.Date.today(),
            })
            # if the project doesn't have a task for the user, create a new one
            if not p.analytic_ids.filtered(lambda x: x.user_id == u) else
            # otherwise, return the task
            (4, p.analytic_ids.filtered(lambda x: x.user_id == u)[0].id)
            for p in projects
            for u in users
        ]

    analytic_ids = fields.Many2many('account.analytic.line', default=_default_analytic_ids)

    user_id = fields.Many2one('res.users', string='User', default=_default_user)
    project_id = fields.Many2one('project.project', string='Project')
    task_id = fields.Many2one('project.task', string='Task')
    # analytic_line_ids = fields.One2many('account.analytic.line', 'planning_id', string='Planning lines')
    # analytic_line_ids = fields.Many2many('account.analytic.line', string='Planning lines')

    _sql_constraints = [('user_project_task_uniq', 'unique (user_id, project_id, task_id)', "The user already planned for project and task.")]

    @api.onchange('project_id', 'task_id')
    def onchange_project_task(self):
        project = self.project_id
        task = self.task_id
        if project and task:
            if project.id != task.project_id.id:
                self.task_id = False
        elif not project:
            self.task_id = False
        elif project and not task:
            self.task_id = project.task_ids.filtered(lambda t: t.standard == True).id

    @api.one
    @api.constrains('project_id', 'task_id')
    def constrain_project_task(self):
        if (self.project_id or self.task_id) and self.analytic_line_ids:
            raise ValidationError(_("You cannot modify planning with entries!"))

    #need to re-check task_id due to it's not getting reset to false while creating or writing through magnus.planning
    @api.model
    def create(self, vals):
        res = super(MagnusPlanningOld, self).create(vals)
        entries = res.analytic_line_ids.filtered(lambda al: not al.task_id)
        entries.write({'task_id':res.task_id.id})
        return res

    @api.multi
    def write(self, vals):
        result = super(MagnusPlanningOld, self).write(vals)
        for res in self:
            entries = res.analytic_line_ids.filtered(lambda al: not al.task_id)
            entries.write({'task_id': res.task_id.id})
        return result

class MagnusPlanning(models.Model):
    _name = "magnus.planning"
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    _order = "id desc"
    _description = "Planning"

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

    name = fields.Char(string="Note", states={'confirm': [('readonly', True)], 'done': [('readonly', True)]})
    employee_id = fields.Many2one('hr.employee', string='Employee', default=_default_employee, required=True)
    user_id = fields.Many2one('res.users', related='employee_id.user_id', string='User', store=True, readonly=True)
    date_from = fields.Date(string='Date From', default=_default_date_from, required=True,
        index=True, readonly=True, states={'new': [('readonly', False)]})
    date_to = fields.Date(string='Date To', default=_default_date_to, required=True,
        index=True, readonly=True, states={'new': [('readonly', False)]})
    planning_ids = fields.One2many('account.analytic.line', 'planning_id',
        string='Planning lines',
        readonly=True, states={
            'draft': [('readonly', False)],
            'new': [('readonly', False)]})
    # state is created in 'new', automatically goes to 'draft' when created. Then 'new' is never used again ...
    # (=> 'new' is completely useless)
    state = fields.Selection([
        ('new', 'New'),
        ('draft', 'Open'),
        ('confirm', 'Waiting Approval'),
        ('done', 'Approved')], default='new', track_visibility='onchange',
        string='Status', required=True, readonly=True, index=True,
        help=' * The \'Open\' status is used when a user is encoding a new and unconfirmed timesheet. '
             '\n* The \'Waiting Approval\' status is used to confirm the timesheet by user. '
             '\n* The \'Approved\' status is used when the users timesheet is accepted by his/her senior.')
    # account_ids = fields.One2many('hr_timesheet_sheet.sheet.account', 'sheet_id', string='Analytic accounts', readonly=True)
    company_id = fields.Many2one('res.company', string='Company')
    department_id = fields.Many2one('hr.department', string='Department',
        default=lambda self: self.env['res.company']._company_default_get())

    week_from = fields.Many2one('date.range', string='week from')
    week_to = fields.Many2one('date.range', string='week to')

    @api.onchange('week_from', 'week_to')
    def onchange_week(self):
        self.date_from = self.week_from.date_start
        self.date_to = self.week_to.date_end



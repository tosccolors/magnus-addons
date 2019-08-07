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

    name = fields.Char(string="Note")
    employee_id = fields.Many2one('hr.employee', string='Employee', default=_default_employee, required=True)
    user_id = fields.Many2one('res.users', related='employee_id.user_id', string='User', store=True, readonly=True)
    date_from = fields.Date(string='Date From', default=_default_date_from, required=True, index=True)
    date_to = fields.Date(string='Date To', default=_default_date_to, required=True, index=True)
    planning_ids = fields.One2many('account.analytic.line', 'planning_id', string='Planning lines')
    company_id = fields.Many2one('res.company', string='Company')
    department_id = fields.Many2one('hr.department', string='Department',
        default=lambda self: self.env['res.company']._company_default_get())
    week_from = fields.Many2one('date.range', string='week from', required=True,index=True)
    week_to = fields.Many2one('date.range', string='week to', required=True,index=True)

    @api.onchange('week_from', 'week_to')
    def onchange_week(self):
        self.date_from = self.week_from.date_start
        self.date_to = self.week_to.date_end

    def unlink_analytic_entries(self):
        analytic = self.planning_ids.filtered(lambda x: x.unit_amount == 0)
        analytic.unlink()
        return True

    @api.model
    def create(self ,vals):
        res = super(MagnusPlanning, self).create(vals)
        self.unlink_analytic_entries()
        return res

    @api.multi
    def write(self, vals):
        res = super(MagnusPlanning, self).write(vals)
        self.unlink_analytic_entries()
        return res


class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'
    _description = 'Analytic Line'

    employee_id = fields.Many2one('hr.employee', string='Employee')


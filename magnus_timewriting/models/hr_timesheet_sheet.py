# -*- coding: utf-8 -*-
# Copyright 2018 Magnus ((www.magnus.nl).)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _, SUPERUSER_ID
from datetime import datetime, timedelta

class HrTimesheetSheet(models.Model):
    _inherit = "hr_timesheet_sheet.sheet"

    def duplicate_last_week(self):
        dt = datetime.now()
        current_employee = self.env['hr.employee'].search([('user_id', '=', self._uid)], limit=1)
        last_week = self.env['date.range'].search([('type_id','=','week'), ('date_start', '=', dt-timedelta(days=dt.weekday()+7))], limit=1)
        if current_employee and last_week:
            last_week_timesheet = self.env['hr_timesheet_sheet.sheet'].search([('employee_id', '=', current_employee.id), ('week_id', '=', last_week.id)], limit=1)
            if last_week_timesheet:
                self.timesheet_ids.unlink()
                self.timesheet_ids = [(0, 0, {'name': '/','project_id': l.project_id.id,'task_id': l.task_id.id})for l in last_week_timesheet.timesheet_ids]

class AccountAnalyticLine(models.Model):
    _inherit = "account.analytic.line"

    sheet_id = fields.Many2one('hr_timesheet_sheet.sheet', compute='_compute_sheet', string='Sheet', store=True, ondelete='cascade')
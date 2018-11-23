# -*- coding: utf-8 -*-
# Copyright 2018 Magnus ((www.magnus.nl).)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _, SUPERUSER_ID
from datetime import datetime, timedelta
from odoo.exceptions import UserError

class HrTimesheetSheet(models.Model):
    _inherit = "hr_timesheet_sheet.sheet"

    def duplicate_last_week(self):
        if self.week_id and self.employee_id:
            ds = self.week_id.date_start
            date_start = datetime.strptime(ds, "%Y-%m-%d").date() - timedelta(days=7)
            date_end = datetime.strptime(ds, "%Y-%m-%d").date() - timedelta(days=1)
            last_week = self.env['date.range'].search([('type_id','=','week'), ('date_start', '=', date_start), ('date_end', '=', date_end)], limit=1)
            if last_week:
                last_week_timesheet = self.env['hr_timesheet_sheet.sheet'].search([('employee_id', '=', self.employee_id.id), ('week_id', '=', last_week.id)], limit=1)
                if last_week_timesheet:
                    self.timesheet_ids.unlink()
                    self.timesheet_ids = [(0, 0, {'date': datetime.strptime(l.date, "%Y-%m-%d") + timedelta(days=7),'name': '/','project_id': l.project_id.id,'task_id': l.task_id.id}) for l in last_week_timesheet.timesheet_ids]
                else:
                    raise UserError(_("You have no timesheet logged for last week. Duration: %s to %s") %(datetime.strftime(date_start, "%d-%b-%Y"), datetime.strftime(date_end, "%d-%b-%Y")))

class AccountAnalyticLine(models.Model):
    _inherit = "account.analytic.line"

    sheet_id = fields.Many2one('hr_timesheet_sheet.sheet', compute='_compute_sheet', string='Sheet', store=True, ondelete='cascade')
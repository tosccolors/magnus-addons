# -*- coding: utf-8 -*-
# Copyright 2018 Magnus ((www.magnus.nl).)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _
from datetime import datetime, timedelta
from odoo.exceptions import ValidationError, Warning

class HrTimesheetSheet(models.Model):
    _inherit = "hr_timesheet_sheet.sheet"

    def merge_leave_request(self, date, data):
        previous_date = datetime.strftime(date - timedelta(days=1), "%Y-%m-%d")
        domain = [
            ('date_to', '=', previous_date),
            ('employee_id', '=', self.employee_id.id),
            ('type', '=', 'remove'),
            ('state', '=', 'written'),
        ]
        previous_leave_request = self.env['hr.holidays'].search(domain)
        if previous_leave_request:
            # Merge LR by updating date_to and number_of_hours_temp
            previous_leave_request.write({'date_to': date, 'number_of_hours_temp': data['number_of_hours_temp'] + previous_leave_request.number_of_hours_temp})
        else:
            # Create new LR from timesheet
            self.env['hr.holidays'].create(data)

    def create_leave_request(self, leave_type, hour, date):
        # Data to create leave requests from timesheet
        data = {
            'name': 'Time report',
            'number_of_hours_temp': hour,
            'holiday_status_id': leave_type,
            'state': 'written',
            'date_from': date,
            'date_to': date,
            'employee_id': self.employee_id.id,
            'type': 'remove'
        }
        # Domain to get LR available in the same date period
        domain = [
            ('date_from', '<=', date),
            ('date_to', '>=', date),
            ('employee_id', '=', self.employee_id.id),
            ('type', '=', 'remove'),
            ('state', 'not in', ['cancel', 'refuse']),
        ]
        leave_request = self.env['hr.holidays'].search(domain)
        if leave_request:
            date_start = datetime.strptime(leave_request.date_from, "%Y-%m-%d %H:%M:%S").date()
            date_end = datetime.strptime(leave_request.date_to, "%Y-%m-%d %H:%M:%S").date()
            date = datetime.strptime(date, "%Y-%m-%d").date()

            if date_start == date_end:
                leave_request.write({'state': 'draft'})
                leave_request.unlink()
                self.merge_leave_request(date, data)

            elif date_start != date_end:
                if date_start == date:
                    # Update LR with date_from
                    leave_request.write({'date_from': date + timedelta(days=1)})
                    self.merge_leave_request(date, data)

                if date_start != date:
                    if date_end == date:
                        self.merge_leave_request(date, data)
                    if date_end != date:
                        # Update LR with date_from
                        leave_request.write({'date_from': date + timedelta(days=1)})
                        self.merge_leave_request(date, data)
                    splitted_leave_request = leave_request.copy(default={'state':leave_request.state})
                    # Update LR with date_to
                    splitted_leave_request.write({'date_to': date - timedelta(days=1), 'date_from': date_start})
        if not leave_request:
            self.env['hr.holidays'].create(data)

    def get_leave_type(self, hour):
        leave_types = self.env['hr.holidays.status'].filtered('date_start').search([], order='date_start')
        if not leave_types:
            raise ValidationError(_('Please create some leave types to apply for leave.\nNote: For one of the selected project the Holiday Consumption is true.'))
        leave_type = False
        for lt in leave_types:
            if not leave_type and lt.remaining_hours > hour:
                leave_type = lt.id
                break
        if not leave_type:
            leave_type = leave_types[-1].id
        return leave_type

    @api.one
    def action_timesheet_done(self):
        res = super(HrTimesheetSheet, self).action_timesheet_done()
        if self.timesheet_ids:
            date_from = datetime.strptime(self.date_from, "%Y-%m-%d").date()
            for i in range(7):
                date = datetime.strftime(date_from + timedelta(days=i), "%Y-%m-%d")
                hour = sum(self.env['account.analytic.line'].search([('date', '=', date), ('sheet_id', '=', self.id), ('sheet_id.employee_id', '=', self.employee_id.id), ('project_id.holiday_consumption', '=', True)]).mapped('unit_amount'))
                if hour:
                    if hour > 8: hour = 8
                    leave_type = self.get_leave_type(hour)
                    self.create_leave_request(leave_type, hour, date)
        return res

    @api.one
    def action_timesheet_draft(self):
        res = super(HrTimesheetSheet, self).action_timesheet_draft()
        leave_request = self.env['hr.holidays'].search([('name', '=', 'Time report'), ('employee_id', '=', self.employee_id.id), ('date_from', '>=', self.week_id.date_start), ('date_from', '<=', self.week_id.date_end), ('type', '=', 'remove'), ('state', '=', 'written')])
        if leave_request:
            leave_request.write({'state': 'draft'})
            leave_request.unlink()
        return res
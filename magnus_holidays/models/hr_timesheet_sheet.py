# -*- coding: utf-8 -*-
# Copyright 2018 Magnus ((www.magnus.nl).)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _
from datetime import datetime, timedelta
from odoo.exceptions import ValidationError, Warning

class HrTimesheetSheet(models.Model):
    _inherit = "hr_timesheet_sheet.sheet"

    @api.one
    def action_timesheet_done(self):
        res = super(HrTimesheetSheet, self).action_timesheet_done()
        if self.timesheet_ids:
            date_from = datetime.strptime(self.date_from, "%Y-%m-%d").date()
            for i in range(7):
                date = datetime.strftime(date_from + timedelta(days=i), "%Y-%m-%d")
                hour = sum(self.env['account.analytic.line'].search([('date', '=', date), ('sheet_id', '=', self.id), ('sheet_id.employee_id', '=', self.employee_id.id), ('project_id.holiday_consumption', '=', True)]).mapped('unit_amount'))

                if hour:
                    leave_types = self.env['hr.holidays.status'].filtered('date_start').search([], order='date_start')
                    if not leave_types:
                        raise ValidationError(_('Please create some leave types to apply for leave.\nNote: For one of the selected project the Holiday Consumption is true.'))
                    leave_type = False
                    for lt in leave_types:
                        if not leave_type and lt.remaining_hours > 0:
                            if hour > lt.remaining_hours:
                                splitted_val = hour - lt.remaining_hours
                                raise ValidationError(_(
                                    'Please split the number of hours %s into %s + %s '
                                    'to deduct %s hour(s) from the leave type %s. Date: %s.')
                                    %(hour, lt.remaining_hours, splitted_val, lt.remaining_hours, lt.name, date ))
                            leave_type = lt.id
                            break
                    if not leave_type:
                        leave_type = leave_types[-1].id

                    data = {
                        'name': "Time report",
                        'employee_id': self.employee_id.id,
                        'date_from': date,
                        'date_to': date,
                        # 'number_of_hours': -hour,
                        'number_of_hours_temp': hour,
                        'type': 'remove',
                        'holiday_status_id': leave_type,
                        'state': 'written'
                    }
                    self.env['hr.holidays'].create(data)
        return res

    @api.one
    def action_timesheet_draft(self):
        res = super(HrTimesheetSheet, self).action_timesheet_draft()
        leave_request = self.env['hr.holidays'].search([('name', '=', 'Time report'), ('employee_id', '=', self.employee_id.id), ('date_from', '>=', self.week_id.date_start), ('date_from', '<=', self.week_id.date_end), ('type', '=', 'remove'), ('state', '=', 'written')])
        if leave_request:
            leave_request.write({'state': 'draft'})
            leave_request.unlink()
        return res
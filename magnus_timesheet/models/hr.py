# -*- coding: utf-8 -*-
# Copyright 2018 Magnus ((www.magnus.nl).)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _

class Employee(models.Model):
    _inherit = "hr.employee"

    @api.one
    def _get_overtime_hours(self):
        self.overtime_hours = sum(self.env['hr_timesheet_sheet.sheet'].search([('employee_id', '=', self.id)]).mapped('overtime_hours'))

    planning_week = fields.Boolean(string="Planning by week")
    timesheet_optional = fields.Boolean('Timesheet optional')
    timesheet_no_8_hours_day = fields.Boolean('Timesheet no 8 hours day')
    overtime_hours = fields.Float(compute="_get_overtime_hours", string='Overtime Hours')
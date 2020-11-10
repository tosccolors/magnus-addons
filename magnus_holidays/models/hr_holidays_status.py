# -*- coding: utf-8 -*-
# Copyright 2018 Magnus ((www.magnus.nl).)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class HrHolidaysStatus(models.Model):
    _inherit = "hr.holidays.status"

    date_end = fields.Datetime(string="Expiry Date", default='2080-12-31 00:00:00')
    is_leave_type_of_wizard = fields.Boolean(string="Is leave type of wizard")

    @api.multi
    def get_hours(self, employee):
        self.ensure_one()
        result = {
            'max_hours': 0,
            'remaining_hours': 0,
            'hours_taken': 0,
            'virtual_remaining_hours': 0,
        }

        holiday_ids = employee.holiday_ids.filtered(lambda x: ((x.state == 'validate' and x.type == 'add') or (x.state == 'written' and x.type == 'remove')) and x.holiday_status_id == self)

        for holiday in holiday_ids:
            hours = holiday.number_of_hours_temp
            if holiday.type == 'add':
                result['virtual_remaining_hours'] += hours
                if holiday.state == 'validate':
                    result['max_hours'] += hours
                    result['remaining_hours'] += hours
            elif holiday.type == 'remove':  # number of hours is negative
                result['virtual_remaining_hours'] -= hours
                if holiday.state == 'written':
                    result['hours_taken'] += hours
                    result['remaining_hours'] -= hours

        return result
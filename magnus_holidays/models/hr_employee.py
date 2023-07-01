# -*- coding: utf-8 -*-
# Copyright 2018 Magnus ((www.magnus.nl).)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _
from odoo.tools.float_utils import float_round

class HrEmployeeBase(models.AbstractModel):
    _inherit = "hr.employee.base"

    current_leave_state = fields.Selection(selection_add=[('written', 'Written')])

    # # @api.multi
    # def _compute_leaves_count(self):
    #     all_leaves = self.env['hr.leave.report'].read_group([
    #         ('employee_id', 'in', self.ids),
    #         ('holiday_status_id.allocation_type', '!=', 'no'),
    #         ('holiday_status_id.active', '=', 'True'),
    #         ('state', '!=', 'refuse')
    #     ], fields=['number_of_days', 'employee_id'], groupby=['employee_id'])
    #     mapping = dict([(leave['employee_id'][0], leave['number_of_days']) for leave in all_leaves])
    #     for employee in self:
    #         employee.leaves_count = float_round(mapping.get(employee.id, 0), precision_digits=2)

    def _compute_leave_status(self):
        # Used SUPERUSER_ID to forcefully get status of other user's leave, to bypass record rule
        holidays = self.env['hr.leave'].sudo().search([
            ('employee_id', 'in', self.ids),
            ('date_from', '<=', fields.Datetime.now()),
            ('date_to', '>=', fields.Datetime.now()),
            ('state', 'not in', ('cancel', 'refuse'))
        ])
        leave_data = {}
        for holiday in holidays:
            leave_data[holiday.employee_id.id] = {}
            leave_data[holiday.employee_id.id]['leave_date_from'] = holiday.date_from.date()
            leave_data[holiday.employee_id.id]['leave_date_to'] = holiday.date_to.date()
            leave_data[holiday.employee_id.id]['current_leave_state'] = holiday.state
            leave_data[holiday.employee_id.id]['current_leave_id'] = holiday.holiday_status_id.id

        for employee in self:
            employee.leave_date_from = leave_data.get(employee.id, {}).get('leave_date_from')
            employee.leave_date_to = leave_data.get(employee.id, {}).get('leave_date_to')
            employee.current_leave_state = leave_data.get(employee.id, {}).get('current_leave_state')
            employee.current_leave_id = leave_data.get(employee.id, {}).get('current_leave_id')
            # updated state written
            employee.is_absent = leave_data.get(employee.id) and leave_data.get(employee.id, {}).get('current_leave_state') in ['validate', 'written']


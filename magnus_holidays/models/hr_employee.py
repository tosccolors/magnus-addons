# -*- coding: utf-8 -*-
# Copyright 2018 Magnus ((www.magnus.nl).)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _

class HrEmployee(models.Model):
    _inherit = "hr.employee"

    @api.multi
    def _compute_leaves_count(self):
        leaves = self.env['hr.holidays'].read_group([
            ('employee_id', 'in', self.ids),
            ('holiday_status_id.limit', '=', False),
            ('state', '!=', 'refuse')],
            fields=['number_of_hours', 'employee_id'],
            groupby=['employee_id']
        )
        mapping = dict(
            [(leave['employee_id'][0], leave['number_of_hours'])
             for leave in leaves]
        )
        for employee in self:
            employee.leaves_count = mapping.get(employee.id)
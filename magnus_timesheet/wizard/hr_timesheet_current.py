# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class HrTimesheetCurrentOpen(models.TransientModel):
    _inherit = 'hr.timesheet.current.open'

    @api.model
    def open_timesheet(self):
        result = super(HrTimesheetCurrentOpen, self).open_timesheet()
        result['context'] = "{'readonly_by_pass': True}"
        if 'res_id' not in result:
            sheets = self.env['hr_timesheet_sheet.sheet'].search([('user_id', '=', self._uid),
                                                                  ('state', 'in', ('draft', 'new', 'open')),
                                                                  ], limit=1, order='week_id')
            if len(sheets) == 1:
                result['res_id'] = sheets.ids[0]
        return result
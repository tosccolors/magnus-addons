# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class HrTimesheetCurrentOpen(models.TransientModel):
    _inherit = 'hr.timesheet.current.open'

    @api.model
    def open_timesheet(self):
        result = super(HrTimesheetCurrentOpen, self).open_timesheet()
        result['context'] = "{'readonly_by_pass': True}"
        return result
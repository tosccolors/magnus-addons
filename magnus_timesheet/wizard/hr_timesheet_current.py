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

class MyWizard(models.Model):
    _name = 'my.wizard'

    def _default_task_ids(self):
        # your list of project should come from the context, some selection
        # in a previous wizard or wherever else
        projects = self.env['project.project'].search([])
        # projects = self.env['project.project'].browse([1, 2, 3])
        # same with users
        users = self.env['res.users'].search([])
        # users = self.env['res.users'].browse([1, 2, 3])
        return [
            (0, 0, {'project_id': p.id, 'user_id': u.id, 'planned_hours': 0})
            # if the project doesn't have a task for the user, create a new one
            if not p.task_ids.filtered(lambda x: x.user_id == u) else
            # otherwise, return the task
            (4, p.task_ids.filtered(lambda x: x.user_id == u)[0].id)
            for p in projects
            for u in users
        ]

    task_ids = fields.One2many('project.task', 'my_wiz_id',default=_default_task_ids)
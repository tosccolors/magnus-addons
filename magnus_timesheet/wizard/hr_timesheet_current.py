# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from datetime import datetime

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

    @api.model
    def open_self_planning(self):
        value = self.open_timesheet_planning()
        value['context']['self_planning'] = True
        return value

    @api.model
    def open_employees_planning(self):
        value = self.open_timesheet_planning(True)
        value['context']['default_is_planning_officer'] = True
        return value

    @api.model
    def open_timesheet_planning(self, is_planning_officer = False):
        view_type = 'form,tree'

        date = datetime.now().date()

        period = self.env['date.range'].search([('type_id.calender_week', '=', False), ('type_id.fiscal_year', '=', False),
             ('type_id.fiscal_month', '=', False), ('date_start', '<=', date), ('date_end', '>=', date)], limit=1)

        domain = [('user_id', '=', self._uid), ('planning_quarter', '=', period.id), ('is_planning_officer', '=', is_planning_officer)]
        planning = self.env['magnus.planning'].search(domain)

        if len(planning) > 1:
            domain = "[('id', 'in', " + str(planning.ids) + "),('user_id', '=', uid)]"
        else:
            domain = "[('user_id', '=', uid)]"
        value = {
            'domain': domain,
            'name': _('Open Planning'),
            'view_type': 'form',
            'view_mode': view_type,
            'res_model': 'magnus.planning',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'context':{'readonly_by_pass': True}
        }
        if len(planning) == 1:
            value['res_id'] = planning.ids[0]
        return value

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
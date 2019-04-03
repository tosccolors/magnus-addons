# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError

class ChangeChargecode(models.TransientModel):
    _name = "change.chargecode"
    _description = "Change Chargecode"

    project_id = fields.Many2one('project.project', 'Project')
    task_id = fields.Many2one('project.task', 'Task')

    @api.onchange('project_id')
    def onchange_project(self):
        res, domain = {}, {}
        if self.project_id:
            tasks = self.project_id.task_ids
            domain['task_id'] = [('id', 'in', tasks.ids)]
            if len(tasks) == 1:
                res['task_id'] = tasks.id
        return {'value': res, 'domain': domain}

    # TODO: aal with km's?
    # TODO: Reverse of correction?
    @api.multi
    def post(self):
        context = self.env.context.copy()
        analytic_ids = context.get('active_ids', [])
        analytic_lines = self.env['account.analytic.line'].search([
            ('id', 'in', analytic_ids),
            ('state', 'in', ['invoiceable','open'])])
        project_id = self.project_id.id
        task_id = self.task_id.id
        for aal in analytic_lines:
            if aal.task_id.id == task_id:
                continue
            unit_amount = aal.unit_amount
            amount = aal.amount
            aal.with_context(cc=True).write({'state': 'change-chargecode'})
            aal.copy(
                default={'sheet_id': False,
                         'ts_line': False,
                         'unit_amount': -unit_amount,
                         'amount': -amount,
                         'state': 'change-chargecode'
                        }
            )
            aal.copy(
                default={'sheet_id': False,
                         'ts_line': False,
                         'amount': aal.get_fee_rate_amount(
                             task_id,
                             aal.user_id.id
                         ) if self.project_id.chargeable else 0.0,
                         'project_id': project_id,
                         'task_id': task_id,
                         'state':'open'
                         })
        return True

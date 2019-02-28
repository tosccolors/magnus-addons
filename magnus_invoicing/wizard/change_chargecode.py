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

    @api.multi
    def post(self):
        context = self.env.context.copy()
        analytic_ids = context.get('active_ids', [])
        analytic_lines = self.env['account.analytic.line'].search([
            ('id', 'in', analytic_ids),
            ('state', 'in', ['invoiceable','approved'])])
        project_id = self.project_id.id
        task_id = self.task_id.id
        for aal in analytic_lines:
            if aal.task_id.id == task_id:
                continue
            amount = aal.amount
            if aal.amount == 0.0:
                amount = aal.get_fee_rate()
            self.env.cr.execute("""
                UPDATE account_analytic_line SET amount = %s, state = '%s' 
                WHERE id = %s
                """ % (amount, 'change-chargecode', aal.id))
            aal.copy(default={'sheet_id': False, 'amount': -amount, 'state': 'change-chargecode'})
            aal.copy(default={'sheet_id': False, 'amount': 0.0, 'project_id': project_id, 'task_id': task_id, 'state':'open'})
        return True

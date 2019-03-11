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
            ('state', 'in', ['invoiceable','open'])])
        project_id = self.project_id.id
        task_id = self.task_id.id
        for aal in analytic_lines:
            if aal.task_id.id == task_id:
                continue
            unit_amount = aal.unit_amount
            amount = aal.amount
            self.env.cr.execute("""
                UPDATE account_analytic_line SET state = '%s' 
                WHERE id = %s
                """ % ('change-chargecode', aal.id))
            aal.copy(default={'sheet_id': False,
                              'unit_amount': -unit_amount,
                              'amount': -amount,
                              'state': 'change-chargecode'})
            aal_new = aal.copy(default={'sheet_id': False,
                                        'amount': 0.0,
                                        'project_id': project_id,
                                        'task_id': task_id,
                                        'state':'open'})
            amount = aal_new.get_fee_rate() if aal.chargeable else 0.0
            self.env.cr.execute("""
                            UPDATE account_analytic_line SET amount = %s 
                            WHERE id = %s
                            """ % (amount, aal_new.id))
        return True

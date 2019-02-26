# -*- coding: utf-8 -*-
# Copyright 2018 Magnus ((www.magnus.nl).)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api



class AccountInvoiceLine(models.Model):
    _inherit = "account.invoice.line"

    analytic_invoice_id = fields.Many2one(
        'analytic.invoice',
        string='Invoice Reference',
        ondelete='cascade',
        index=True
    )
    user_id = fields.Many2one(
        'res.users',
        'Timesheet User',
        index = True
    )
    analytic_policy_always_posted = fields.Boolean('Analytic Policy')

    @api.onchange('account_id')
    def onchange_account_id(self):
        self.analytic_policy_always_posted = False
        if self.account_id and self.account_id.user_type_id and self.account_id.user_type_id.analytic_policy:
            if self.account_id.user_type_id.analytic_policy in ['always', 'posted']:
                self.analytic_policy_always_posted = True

class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    @api.multi
    def _get_timesheet_by_group(self):
        self.ensure_one()
        aal_ids = []
        analytic_invoice_ids = self.invoice_line_ids.mapped('analytic_invoice_id')
        for analytic_invoice in analytic_invoice_ids:
            for grp_line in analytic_invoice.user_total_ids:
                aal_ids += grp_line.children_ids
        userProject = {}
        for aal in aal_ids:
            project_id, user_id = aal.project_id if aal.project_id else aal.task_id.project_id , aal.user_id
            if project_id.correction_charge and project_id.specs_invoice_report:
                if (project_id, user_id) in userProject:
                    userProject[(project_id, user_id)] = userProject[(project_id, user_id)] + [aal]
                else:
                    userProject[(project_id, user_id)] = [aal]
        return userProject


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    type = fields.Selection(selection_add=[('wip', 'WIP')])

        



# -*- coding: utf-8 -*-
# Copyright 2018 Magnus ((www.magnus.nl).)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api

class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    customer_charge_expense = fields.Boolean('Charge Expense To Customer', index=True)

    @api.multi
    def _prepare_analytic_line(self):
        analytic_line = super(AccountMoveLine, self)._prepare_analytic_line()
        if self.partner_id:
            context = self._context
            if context.get('active_model') == 'hr.expense':
                user_id = self.env['res.users'].search([('partner_id','=',self.partner_id.id)],limit=1)
                if user_id:
                    user_id = user_id.id
                else:
                    user_id = self._uid
                analytic_line[0]['user_id'] = user_id
        analytic_line[0]['customer_charge_expense'] = self.customer_charge_expense
        return analytic_line

class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    customer_charge_expense = fields.Boolean('Charge Expense To Customer', index=True)
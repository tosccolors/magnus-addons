# -*- coding: utf-8 -*-
# Copyright 2018 Magnus ((www.magnus.nl).)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api

class HrExpense(models.Model):
    _inherit = 'hr.expense'

    @api.model
    def update_expense(self):
        expense_obj = self.env['hr.expense']
        for expense in expense_obj.search([('state', '=', 'draft'), 'operating_unit_id', '=', False]):
            expense.submit_expenses()

        for expense in expense_obj.search([('operating_unit_id', '=', False), ('analytic_account_id', '!=', False)]):
            expense.operating_unit_id = expense.analytic_account_id.operating_unit_ids and expense.analytic_account_id.operating_unit_ids.ids[0]
        return True



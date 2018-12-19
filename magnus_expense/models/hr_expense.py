# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

class HrExpense(models.Model):
    _inherit = "hr.expense"

    @api.multi
    def submit_expenses(self):
        if any(expense.state != 'draft' for expense in self):
            raise UserError(_("You cannot report twice the same line!"))
        if len(self.mapped('employee_id')) != 1:
            raise UserError(_("You cannot report expenses for different employees in the same report!"))
        expense_sheet = self.env['hr.expense.sheet'].create({'expense_line_ids':[(6, 0, [line.id for line in self])], 'employee_id':self[0].employee_id.id, 'name': self[0].name if len(self.ids) == 1 else ''})
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'hr.expense.sheet',
            'target': 'current',
            'res_id': expense_sheet.id
        }

    @api.multi
    def view_sheet(self):
        res = super(HrExpense, self).view_sheet()
        res['flags'] = {'initial_mode': 'edit'}
        return res


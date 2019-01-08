# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

class HrExpense(models.Model):
    _inherit = "hr.expense"

    @api.depends('sheet_id.state')
    def _get_sheet_state(self):
        for exp in self:
            if exp.sheet_id:
                exp.sheet_state = exp.sheet_id.state

    sheet_state = fields.Char(compute='_get_sheet_state', string='Sheet Status', help='Expense Report State', store=True)

    @api.multi
    def action_move_create(self):
        '''
        inherited function that is called when trying to create the accounting entries related to an expense
        '''
        res = super(HrExpense, self).action_move_create()
        for expense in self:
            if expense.analytic_account_id and expense.analytic_account_id.operating_unit_ids:
                ou = expense.analytic_account_id.operating_unit_ids[0]
                if ou and expense.sheet_id.account_move_id:
                    expense.sheet_id.account_move_id.operating_unit_id = ou.id
        return res

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


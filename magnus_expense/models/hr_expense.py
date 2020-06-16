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
    customer_charge_expense = fields.Boolean('Charge Expense To Customer', index=True)
    analytic_tag_ids = fields.Many2many('account.analytic.tag', string='WKR')
    state = fields.Selection(selection_add=[('revise', 'To Be Revise')])

    @api.onchange('product_id')
    def _onchange_product_id(self):
        # Inherited this onchange function to reload the same value to the field 'name'.
        name = self.name
        res = super(HrExpense, self)._onchange_product_id()
        self.name = name
        return res

    @api.model
    def default_get(self, default_fields):
        res = super(HrExpenseSheet, self).default_get(default_fields) or {}
        res['journal_id'] = self.env.user.company_id.decl_journal_id.id
        return res

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
        expense_sheet = self.env['hr.expense.sheet'].create({'expense_line_ids':[(6, 0, [line.id for line in self])], 'employee_id':self[0].employee_id.id, 'name': self[0].name if len(self.ids) == 1 else '','operating_unit_id':self[0].operating_unit_id.id})
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

    @api.onchange('analytic_account_id','operating_unit_id')
    def anaytic_account_change(self):
        if self.analytic_account_id and self.analytic_account_id.linked_operating_unit:
            self.operating_unit_id = self.analytic_account_id.operating_unit_ids.ids[0]

    def _prepare_move_line(self, line):
        move_line = super(HrExpense, self)._prepare_move_line(line)
        if move_line.get('analytic_account_id', False):
            move_line.update({'customer_charge_expense': self.customer_charge_expense})
        if self.analytic_tag_ids:
            move_line.update({'analytic_tag_ids': [(6, 0, self.analytic_tag_ids.ids)]})
        return move_line

    @api.multi
    def write(self, vals):
        if vals.get('operating_unit_id', False):
            sheet_id = vals['sheet_id'] if vals.get('sheet_id', False) else self.sheet_id.id
            if sheet_id:
                expense_sheet = self.env['hr.expense.sheet'].browse(sheet_id)
                expense_sheet.write({'operating_unit_id':vals.get('operating_unit_id')})
        res = super(HrExpense, self).write(vals)
        return res

class HrExpenseSheet(models.Model):
    _inherit = "hr.expense.sheet"

    state = fields.Selection(selection_add=[('revise', 'To Be Revise')])

    @api.multi
    def revise_expense(self):
        expenses = self.expense_line_ids.filtered(lambda x: x.state == 'reported')
        self.write({'state': 'revise'})
        expenses.write({'state':'revise'})

    @api.multi
    def expense_revised(self):
        expenses = self.expense_line_ids.filtered(lambda x: x.state == 'revise')
        expenses.write({'state': 'reported'})
        self.write({'state': 'approve'})

    @api.onchange('expense_line_ids')
    def onchange_expense_line_ids(self):
        if self.expense_line_ids and self.expense_line_ids[0].operating_unit_id:
            if not self.operating_unit_id or (self.operating_unit_id and len(self.expense_line_ids) == 1):
                self.operating_unit_id = self.expense_line_ids[0].operating_unit_id.id
        else:
            self.operating_unit_id = False
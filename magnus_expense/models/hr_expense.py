# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import email_split, float_is_zero

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
    def action_submit_expenses(self):
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
    def action_view_sheet(self):
        res = super(HrExpense, self).action_view_sheet()
        res['flags'] = {'initial_mode': 'edit'}
        return res

    @api.onchange('analytic_account_id','operating_unit_id')
    def anaytic_account_change(self):
        if self.analytic_account_id and self.analytic_account_id.linked_operating_unit:
            self.operating_unit_id = self.analytic_account_id.operating_unit_ids.ids[0]

    # <----code commeted fuction not in odoo12-------->
    # def _prepare_move_line(self, line):
    #     move_line = super(HrExpense, self)._prepare_move_line(line)
    #     if move_line.get('analytic_account_id', False):
    #         move_line.update({'customer_charge_expense': self.customer_charge_expense})
    #     if self.analytic_tag_ids:
    #         move_line.update({'analytic_tag_ids': [(6, 0, self.analytic_tag_ids.ids)]})
    #     return move_line

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

    # added new status Approved by partner

    state = fields.Selection([('draft', 'Draft'),
                              ('submit', 'Submitted'),
                              ('approve', 'Approved By Manager'),
                              ('approve_partner','Approved By Partner'),
                              ('post', 'Posted'),
                              ('done', 'Paid'),
                              ('cancel', 'Refused'),
                              ('revise', 'To Be Revise')
                              ], string='Status', index=True, readonly=True, track_visibility='onchange', copy=False,
                             default='submit', required=True,
                             help='Expense Report State')

    # state = fields.Selection(selection_add=[('revise', 'To Be Revise')]

    @api.model
    def default_get(self, default_fields):
        res = super(HrExpenseSheet, self).default_get(default_fields) or {}
        res['journal_id'] = self.env.user.company_id.decl_journal_id.id
        return res

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

   # updated by expense sheets are approved by partner group will goto status Approved By Partner

    @api.multi
    def approve_partner_expense_sheets(self):
        if not self.env.user.has_group('magnus_expense.group_hr_expense_partner'):
            raise UserError(_("Only Partner can approve expenses"))
        self.write({'state': 'approve_partner', 'user_id': self.env.user.id})


    # updated by expense sheets move create which are in  status Approved By Partner

    @api.multi
    def action_partner_sheet_move_create(self):
        if any(sheet.state != 'approve_partner' for sheet in self):
            raise UserError(_("You can only generate accounting entry for approved expense(s)."))

        if any(not sheet.journal_id for sheet in self):
            raise UserError(_("Expenses must have an expense journal specified to generate accounting entries."))

        expense_line_ids = self.mapped('expense_line_ids') \
            .filtered(lambda r: not float_is_zero(r.total_amount, precision_rounding=(
                    r.currency_id or self.env.user.company_id.currency_id).rounding))
        res = expense_line_ids.action_move_create()

        if not self.accounting_date:
            self.accounting_date = self.account_move_id.date

        if self.payment_mode == 'own_account' and expense_line_ids:
            self.write({'state': 'post'})
        else:
            self.write({'state': 'done'})
        return res

    # # adding server action function for the menuitem partner approval
    # @api.multi
    # def partner_approval_menu_action(self):
    #     get_logged_user_emp_id = self.env['hr.employee'].sudo().search([('user_id', '=', self.env.user.id)])
    #     child_departs = self.env['hr.department'].sudo().search(
    #         [('id', 'child_of', get_logged_user_emp_id.department_id.ids)]).mapped('id')
    #     return {
    #         'name': 'Partner Approval',
    #         'type': 'ir.actions.act_window',
    #         'view_type': 'form',
    #         'view_mode': 'tree,kanban,form,pivot,graph',
    #         'domain': "['&',('employee_id.department_id.id', 'in', %s),('state','=','approve')]" % child_departs,
    #         'res_model': 'hr.expense.sheet',
    #         'target': 'current'
    #         }
    
    @api.one
    @api.constrains('expense_line_ids', 'employee_id')
    def _check_employee(self):
        employee_ids = self.expense_line_ids.mapped('employee_id')
        # checking the state revised and group Manager
        if self.state== 'revise':
            if self.env.user.has_group('hr_expense.group_hr_expense_manager'):
                # Updating the expense_line_ids with employee_id
                for emp in self.expense_line_ids:
                    emp.employee_id=self.employee_id
                return True
        if len(employee_ids) > 1 or (len(employee_ids) == 1 and employee_ids != self.employee_id):
            raise ValidationError(_('You cannot add expense lines of another employee.'))
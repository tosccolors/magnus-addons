# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import re

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import email_split, float_is_zero

import odoo.addons.decimal_precision as dp

class HrExpense(models.Model):
    _inherit = 'hr.expense'
    
    is_from_crdit_card = fields.Boolean("is From Credit Card")

    @api.model
    def default_get(self, fields):
        rec = super(HrExpense, self).default_get(fields)
        if self._context.get("from_credi_card_expense"):
            rec.update({'is_from_crdit_card': True})
        return rec
    
    @api.model
    def create(self,vals):
        if self._context.get("from_credi_card_expense"):
            vals.update({'is_from_crdit_card':True,'payment_mode':'company_account'})
        else:
            vals.update({'is_from_crdit_card':False,'payment_mode':'own_account'})
        if vals.get('company_id'):
            res_company = self.env['res.company'].search([('id','=',vals.get('company_id'))])
            if res_company:
                vals.update({'currency_id':res_company.currency_id.id})
        return super(HrExpense,self).create(vals)
    
    @api.multi
    def submit_expenses(self):
        if any(expense.state != 'draft' for expense in self):
            raise UserError(_("You cannot report twice the same line!"))
        if len(self.mapped('employee_id')) != 1:
            raise UserError(_("You cannot report expenses for different employees in the same report!"))
        expense_sheet = self.env['hr.expense.sheet'].create({'expense_line_ids':[(6, 0, [line.id for line in self])], 'employee_id':self[0].employee_id.id, 'name': self[0].name if len(self.ids) == 1 else '','operating_unit_id':self[0].operating_unit_id.id,
                                                             'is_from_crdit_card':self.is_from_crdit_card})
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'hr.expense.sheet',
            'target': 'current',
            'res_id': expense_sheet.id
        }
        
    @api.multi
    def action_move_create(self):
        '''
        main function that is called when trying to create the accounting entries related to an expense
        '''
        for expense in self:
            if expense.is_from_crdit_card:
                journal = expense.sheet_id.company_id.creditcard_decl_journal_id
            else:
                journal = expense.sheet_id.company_id.decl_journal_id
#             journal = expense.sheet_id.bank_journal_id if expense.payment_mode == 'company_account' else expense.sheet_id.journal_id
            #create the move that will contain the accounting entries
            acc_date = expense.sheet_id.accounting_date or expense.date
            move = self.env['account.move'].create({
                'journal_id': journal.id,
                'company_id': self.env.user.company_id.id,
                'date': acc_date,
                'ref': expense.sheet_id.name,
                # force the name to the default value, to avoid an eventual 'default_name' in the context
                # to set it to '' which cause no number to be given to the account.move when posted.
                'name': '/',
            })
            company_currency = expense.company_id.currency_id
            diff_currency_p = expense.currency_id != company_currency
            #one account.move.line per expense (+taxes..)
            move_lines = expense._move_line_get()
            
            #create one more move line, a counterline for the total on payable account
            payment_id = False
            total, total_currency, move_lines = expense._compute_expense_totals(company_currency, move_lines, acc_date)
            if expense.is_from_crdit_card:
                if not expense.sheet_id.company_id.creditcard_decl_journal_id:
                    raise UserError(_("No credit account found for the %s journal, please configure one.") % (expense.sheet_id.bank_journal_id.name))
#                 emp_account = expense.sheet_id.bank_journal_id.default_credit_account_id.id
                emp_account = expense.sheet_id.company_id.creditcard_decl_journal_id.default_credit_account_id.id
                
                journal = expense.sheet_id.company_id.creditcard_decl_journal_id
                #create payment
                payment_methods = (total < 0) and journal.outbound_payment_method_ids or journal.inbound_payment_method_ids
                journal_currency = journal.currency_id or journal.company_id.currency_id
                payment = self.env['account.payment'].create({
                    'payment_method_id': payment_methods and payment_methods[0].id or False,
                    'payment_type': total < 0 and 'outbound' or 'inbound',
                    'partner_id': expense.employee_id.address_home_id.commercial_partner_id.id,
                    'partner_type': 'supplier',
                    'journal_id': journal.id,
                    'payment_date': expense.date,
                    'state': 'reconciled',
                    'currency_id': diff_currency_p and expense.currency_id.id or journal_currency.id,
                    'amount': diff_currency_p and abs(total_currency) or abs(total),
                    'name': expense.name,
                })
                payment_id = payment.id
            else:
#                 if not expense.sheet_id.company_id.decl_journal_id.default_credit_account_id:
#                     raise UserError(_("No credit account found for the %s journal, please configure one. ") % (expense.sheet_id.company_id.decl_journal_id.name))
                if not expense.employee_id.address_home_id:
                     raise UserError(_("No Home Address found for the employee %s, please configure one.") % (expense.employee_id.name))
                emp_account = expense.employee_id.address_home_id.property_account_payable_id.id

#                 emp_account = expense.sheet_id.company_id.decl_journal_id.default_credit_account_id.id
            aml_name = expense.employee_id.name + ': ' + expense.name.split('\n')[0][:64]
            move_lines.append({
                    'type': 'dest',
                    'name': aml_name,
                    'price': total,
                    'account_id': emp_account,
                    'date_maturity': acc_date,
                    'amount_currency': diff_currency_p and total_currency or False,
                    'currency_id': diff_currency_p and expense.currency_id.id or False,
                    'payment_id': payment_id,
                    })
            #convert eml into an osv-valid format
            lines = map(lambda x: (0, 0, expense._prepare_move_line(x)), move_lines)
            move.with_context(dont_create_taxes=True).write({'line_ids': lines})
            expense.sheet_id.write({'account_move_id': move.id})
            #updating the line_ids 1st line_id OU with creditcard_decl_journal_id OU
            if expense.is_from_crdit_card:
                ou = expense.sheet_id.company_id.creditcard_decl_journal_id.operating_unit_id
                if ou and expense.sheet_id.account_move_id:
                    expense.sheet_id.account_move_id.line_ids[0].operating_unit_id = ou.id
            move.post()
            if expense.payment_mode == 'company_account':
                expense.sheet_id.paid_expense_sheets()
        return True
        
class HrExpenseSheet(models.Model):

    _inherit = "hr.expense.sheet"
    
    is_from_crdit_card = fields.Boolean("is From Credit Card")
    
    @api.model
    def default_get(self, fields):
        rec = super(HrExpenseSheet, self).default_get(fields)
        if self._context.get("from_credi_card_expense"):
            rec.update({'is_from_crdit_card':True})
        return rec


    @api.model
    def create(self,vals):
        if self._context.get("from_credi_card_expense"):
            vals.update({'is_from_crdit_card':True})
        res = super(HrExpenseSheet,self).create(vals)
        if res.is_from_crdit_card:
            for line in res.expense_line_ids:
                line.write({'is_from_crdit_card':True,'payment_mode':'company_account'})
        return res
    @api.multi
    def write(self,vals):
        if self.filtered('is_from_crdit_card'):
            credit_card_exp = True
        else:
            credit_card_exp = False
        if vals.get('expense_line_ids'):
            line_list = vals.get('expense_line_ids')[0][2]
            for expense in self.env['hr.expense'].browse(line_list):
                expense.write({'is_from_crdit_card':credit_card_exp,'payment_mode':'company_account'})
        for credit_line in self.filtered('is_from_crdit_card'):
            for line in credit_line.expense_line_ids:
                line.write({'is_from_crdit_card':credit_card_exp,'payment_mode':'company_account'})
        return super(HrExpenseSheet,self).write(vals)
    
    @api.multi
    def action_partner_sheet_move_create(self):
        if any(sheet.state != 'approve_partner' for sheet in self):
            raise UserError(_("You can only generate accounting entry for approved expense(s)."))
        
        if self.is_from_crdit_card:
            for sheet in self:
                if not sheet.company_id.creditcard_decl_journal_id.id:
                    raise UserError(_("Please set Credit Card Expense journal in company configuration"))
        else:
            for sheet in self:
                if not sheet.company_id.decl_journal_id.id:
                    raise UserError(_("Please set Declaration Journal in company configuration"))
            
        expense_line_ids = self.mapped('expense_line_ids')\
            .filtered(lambda r: not float_is_zero(r.total_amount, precision_rounding=(r.currency_id or self.env.user.company_id.currency_id).rounding))
        res = expense_line_ids.action_move_create()
        if not self.accounting_date:
            self.accounting_date = self.account_move_id.date

        if self.payment_mode == 'own_account' and expense_line_ids:
            self.write({'state': 'post'})
        else:
            self.write({'state': 'done'})
        return res
    
    @api.one
    @api.constrains('expense_line_ids')
    def _check_amounts(self):
        # DO NOT FORWARD-PORT! ONLY FOR v10
        positive_lines = any([l.total_amount > 0 for l in self.expense_line_ids])
        negative_lines = any([l.total_amount < 0 for l in self.expense_line_ids])
#         if positive_lines and negative_lines:
#             raise ValidationError(_('You cannot have a positive and negative amounts on the same expense report.'))

    # adding server action function for the menuitem partner approval
    @api.multi
    def partner_credit_card_approval_menu_action(self):
        get_logged_user_emp_id = self.env['hr.employee'].sudo().search([('user_id', '=', self.env.user.id)])
        child_departs = self.env['hr.department'].sudo().search(
            [('id', 'child_of', get_logged_user_emp_id.department_id.ids)]).mapped('id')
        return {
            'name': 'Credit Card Partner Approval',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,kanban,form,pivot,graph',
            'domain': "['&','&',('employee_id.department_id.id', 'in', %s),('state','=','approve'),('is_from_crdit_card', '=', True)]" % child_departs,
            'res_model': 'hr.expense.sheet',
            'context': "{'from_credi_card_expense':True}",
            'target': 'current'
        }





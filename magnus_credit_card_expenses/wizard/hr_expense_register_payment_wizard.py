# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from werkzeug import url_encode

class HrExpenseRegisterPaymentWizard(models.TransientModel):
    _inherit= "hr.expense.sheet.register.payment.wizard"
    _description = "Hr Expense Register Payment wizard"

    
    # @api.one
    @api.constrains('amount')
    def _check_amount(self):
        if not self.amount > 0.0:
            print ("removed...")
            raise ValidationError(_('The payment amount must be strictly positive.'))



class account_abstract_payment(models.AbstractModel):
    _inherit = "account.abstract.payment"
    _description = "Contains the logic shared between models which allows to register payments"


    # @api.one
    @api.constrains('amount')
    def _check_amount(self):
        if not self.amount > 0.0:
            print ("removed")
            raise ValidationError(_('The payment amount must be strictly positive.'))
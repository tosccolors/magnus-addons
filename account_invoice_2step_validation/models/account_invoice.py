# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2013 Eurogroup Consulting NL (<http://eurogroupconsulting.nl>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################


from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


# added by -- deep
class Invoice(models.Model):
    _inherit = ['account.invoice']

    @api.one
    @api.depends('invoice_line_ids.price_subtotal', 'tax_line_ids.amount', 'currency_id', 'company_id', 'date_invoice', 'type')
    def _compute_amount(self):

        # -- deep
        # Functionality for updating "verif_tresh_exceeded" are split b/w Company & Invoice Objects

        self.amount_untaxed = sum(line.price_subtotal for line in self.invoice_line_ids)
        self.amount_tax = sum(line.amount for line in self.tax_line_ids)
        self.amount_total = self.amount_untaxed + self.amount_tax
        amount_total_company_signed = self.amount_total
        amount_untaxed_signed = self.amount_untaxed
        if self.currency_id and self.company_id and self.currency_id != self.company_id.currency_id:
            currency_id = self.currency_id.with_context(date=self.date_invoice)
            amount_total_company_signed = currency_id.compute(self.amount_total, self.company_id.currency_id)
            amount_untaxed_signed = currency_id.compute(self.amount_untaxed, self.company_id.currency_id)
        sign = self.type in ['in_refund', 'out_refund'] and -1 or 1
        self.amount_total_company_signed = amount_total_company_signed * sign
        self.amount_total_signed = self.amount_total * sign
        self.amount_untaxed_signed = amount_untaxed_signed * sign

        if self.company_id.verify_setting < self.amount_untaxed:
            self.verif_tresh_exceeded = True
        else:
            self.verif_tresh_exceeded = False


    state = fields.Selection([
        ('draft','Draft'),
        ('proforma','Pro-forma'),
        ('proforma2','Pro-forma'),
        ('open','Open'),
        ('auth','Authorized'),
        ('verified','Verified'),
        ('paid','Paid'),
        ('cancel','Cancelled'),
        ],'Status', index=True, readonly=True, track_visibility='onchange',
        help=' * The \'Draft\' status is used when a user is encoding a new and unconfirmed Invoice. \
        \n* The \'Pro-forma\' when invoice is in Pro-forma status,invoice does not have an invoice number. \
        \n* The \'Authorized\' status is used when invoice is already posted, but not yet confirmed for payment. \
        \n* The \'Verified\' status is used when invoice is already authorized, but not yet confirmed for payment, because it is of higher value than Company Verification treshold. \
        \n* The \'Open\' status is used when user create invoice,a invoice number is generated.Its in open status till user does not pay invoice. \
        \n* The \'Paid\' status is set automatically when the invoice is paid. Its related journal entries may or may not be reconciled. \
        \n* The \'Cancelled\' status is used when user cancel invoice.')

    payment_term = fields.Many2one('account.payment.term', 'Payment Terms',readonly=True, states={'draft':[('readonly',False)]},
        help="If you use payment terms, the due date will be computed automatically at the generation "\
            "of accounting entries. If you keep the payment term and the due date empty, it means direct payment. "\
            "The payment term may compute several due dates, for example 50% now, 50% in one month.",)# groups="account.group_account_invoice")

    user_id = fields.Many2one('res.users', 'Salesperson', readonly=True, track_visibility='onchange', states={'draft':[('readonly',False)],'open':[('readonly',False)]})
    reference = fields.Char('Invoice Reference', size=64, help="The partner reference of this invoice.",)# groups="account.group_account_invoice")

    # TODO: FIXME
    # amount_to_pay = fields.related('residual',
    #     type='float', string='Amount to be paid',
    #     help='The amount which should be paid at the current date.',)# groups="account.group_account_invoice")

    verif_tresh_exceeded = fields.Boolean(string='Verification Treshold',
        store=True, readonly=True, compute='_compute_amount', track_visibility='always', copy=False)


    @api.multi
    def action_date_assign(self):
        for inv in self:
            if not inv.date_due:
                inv._onchange_payment_term_date_invoice()
        return True

    # -- added by deep
    # no need to override the method: action_move_create
    # Invoice date is set either of Record's date or today's date

    # Overridden:
    @api.multi
    def invoice_validate(self):
        self.write({'state':'open'})
        return True

    @api.multi
    def action_invoice_auth(self):
        self.write({'state':'auth'})

    @api.multi
    def action_unauthorize(self):
        self.write({'state':'open'})

    @api.multi
    def action_invoice_verify(self):
        self.write({'state':'verified'})

    @api.multi
    def action_unverify(self):
        return self.action_invoice_auth()

    #Overridden:
    @api.multi
    def action_invoice_cancel(self):
        if self.filtered(lambda inv: inv.state not in ['proforma2', 'draft', 'open', 'auth']):
            raise UserError(_("Invoice must be in draft, Pro-forma or open state in order to be cancelled."))
        return self.action_cancel()


# TODO: FIXME: Expense-Move relation no longer exists
# -- deep
# Brought from NSM_Expense
# domain in payment_order to filter Verfied Invoice
# class Move(models.Model):
#     _inherit = ['account.move']
#
#     expense_id = fields.One2many('hr.expense', 'account_move_id', 'Expense', readonly=True)
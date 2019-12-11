# -*- coding: utf-8 -*-
# Copyright 2018 Magnus ((www.magnus.nl).)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _
from datetime import datetime, timedelta
from odoo.exceptions import UserError, ValidationError

class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    state = fields.Selection([
        ('draft', 'Draft'),
        ('open', 'Confirmed'),
        ('delayed', 'Delayed'),
        ('invoiceable', 'To be Invoiced'),
        ('progress', 'In Progress'),
        ('invoice_created', 'Invoice Created'),
        ('invoiced', 'Invoiced'),
        ('write-off', 'Write-Off'),
        ('change-chargecode', 'Change-Chargecode'),
        ('invoiced-by-fixed', 'Invoiced by Fixed'),
        ('expense-invoiced', 'Expense Invoiced')
    ],
        string='Status',
        readonly=True,
        copy=False,
        index=True,
        track_visibility='onchange',
        default='draft'
    )
    user_total_id = fields.Many2one(
        'analytic.user.total',
        string='Summary Reference',
        index=True
    )

    @api.multi
    def write(self, vals):
        #Condition to check if sheet_id is already exists!
        if 'sheet_id' in vals and vals['sheet_id'] == False and self.filtered('sheet_id'):
            raise ValidationError(_(
                'Timesheet link can not be deleted for %s.\n '
            ) % self)

        # don't call super if only state has to be updated
        if self and 'state' in vals and len(vals) == 1:
            state = vals['state']
            cond, rec = ("IN", tuple(self.ids)) if len(self) > 1 else ("=",
                       self.id)
            self.env.cr.execute("""
                               UPDATE %s SET state = '%s' WHERE id %s %s
                               """ % (self._table, state, cond, rec))
            self.env.invalidate_all()
            vals.pop('state')
            return True

        if self.filtered('ts_line') and not (
                'unit_amount' in vals or
                'product_uom_id' in vals or
                'sheet_id' in vals or
                'date' in vals or
                'project_id' in vals or
                'task_id' in vals or
                'user_id' in vals or
                'name' in vals or
                'ref' in vals):

            #always copy context to keep other context reference
            context = self.env.context.copy()
            context.update({'analytic_check_state': True})
            return super(AccountAnalyticLine, self.with_context(context)).write(
                vals)
        return super(AccountAnalyticLine, self).write(vals)

    def _check_state(self):
        """
        to check if any lines computes method calls allow to modify
        :return: True or super
        """
        context = self.env.context.copy()
        if 'analytic_check_state' in context \
                or 'active_invoice_id' in context:
            return True
        return super(AccountAnalyticLine, self)._check_state()


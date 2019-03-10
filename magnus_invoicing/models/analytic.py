# -*- coding: utf-8 -*-
# Copyright 2018 Magnus ((www.magnus.nl).)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _
from datetime import datetime, timedelta

class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'


    state = fields.Selection([
        ('draft', 'Draft'),
        ('open', 'Confirmed'),
        ('delayed', 'Delayed'),
        ('invoiceable', 'To be Invoiced'),
        ('progress', 'In Progress'),
        ('invoiced', 'Invoiced'),
        ('write_off', 'Write-Off'),
        ('change-chargecode', 'Change-Chargecode'),
    ],
        string='Status',
        readonly=True,
        copy=False,
        index=True,
        track_visibility='onchange',
        default='draft'
    )

    invoiced = fields.Boolean(
        'Invoiced'
    )
    invoiceable = fields.Boolean(
        'Invoiceable'
    )

    @api.multi
    def write(self, vals):
        state_lines = self.env['account.analytic.line']
        for aal in self:
            if 'state' in vals:
                state_lines |= aal
        state_lines = state_lines.with_context(state=True)
        super(AccountAnalyticLine, state_lines).write(vals)
        super(AccountAnalyticLine, self - state_lines).write(vals)
        return True

    def _check_state(self):
        """
        to check if any lines computes method calls allow to modify
        :return: True or super
        """
        context = self.env.context.copy()
        if not 'active_model' in context \
                or 'active_invoice_id' in context \
                or 'cc' in context and context['cc']\
                or 'state' in context and context['state']:
            return True
        return super(AccountAnalyticLine, self)._check_state()


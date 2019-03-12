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

    @api.multi
    def write(self, vals):
        if 'state' in vals:
            state = vals['state']
            cond, rec = ("IN", tuple(self.ids)) if len(self) > 1 else ("=", self.id)
            self.env.cr.execute("""
                                UPDATE %s SET state = '%s' WHERE id %s %s
                                """ % (self._table, state, cond, rec))
            self.env.invalidate_all()
            vals.pop('state')
        return super(AccountAnalyticLine, self).write(vals) if vals else True

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


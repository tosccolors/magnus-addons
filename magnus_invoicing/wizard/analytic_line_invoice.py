# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.addons.queue_job.job import job, related_action
from odoo.addons.queue_job.exception import FailedJobError
from unidecode import unidecode


class AnalyticLineStatus(models.TransientModel):
    _name = "analytic.line.status"
    _description = "Analytic line Status"

    name = fields.Selection([
        ('invoiceable', 'To be invoiced'),
        ('delayed', 'Delayed'),
    ], string='Lines to be')

    @api.one
    def analytic_invoice_lines(self):
        context = self.env.context.copy()
        analytic_ids = context.get('active_ids',[])
        analytic_lines = self.env['account.analytic.line'].browse(analytic_ids)
        status = self.name
        entries = analytic_lines.filtered(lambda a: a.invoiced != True and a.state not in ('draft','invoiced'))
        if entries:
            data = {'state':status,'invoiceable':False}
            context.update({'UpdateState': True})
            if status == 'invoiceable':
                data['invoiceable'] = True

            entries.with_context(context).write(data)
        return True


# -*- coding: utf-8 -*-
# Copyright 2018 Magnus ((www.magnus.nl).)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
from odoo.tools.translate import _

class HrTimesheetSheet(models.Model):
    _inherit = "hr_timesheet_sheet.sheet"

    @api.multi
    def action_timesheet_done(self):
        """
        On timesheet confirmed update analytic state to confirmed
        :return: Super
        """
        context = self.env.context.copy()
        res = super(HrTimesheetSheet, self).action_timesheet_done()
        # context.update({'UpdateState':True})
        # self.timesheet_ids.with_context(context).write({'state':'open'})
        if self.timesheet_ids:
            cond = '='
            rec = self.timesheet_ids.ids[0]
            if len(self.timesheet_ids) > 1:
                cond = 'IN'
                rec = tuple(self.timesheet_ids.ids)
            self.env.cr.execute("""
                    UPDATE account_analytic_line SET state = 'open' WHERE id %s %s
            """ % (cond, rec))
        return res

    @api.multi
    def action_timesheet_draft(self):
        """
        On timesheet reset draft check analytic shouldn't be in invoiced
        :return: Super
        """
        if self.timesheet_ids.filtered('invoiced'):
            raise UserError(_('You cannot modify an entry in a invoiced timesheet'))
        res = super(HrTimesheetSheet, self).action_timesheet_draft()

        if self.timesheet_ids:
            cond = '='
            rec = self.timesheet_ids.ids[0]
            if len(self.timesheet_ids) > 1:
                cond = 'IN'
                rec = tuple(self.timesheet_ids.ids)
            self.env.cr.execute("""
                    UPDATE account_analytic_line SET state = 'draft', invoiceable = false WHERE id %s %s
            """ % (cond, rec))
        return res
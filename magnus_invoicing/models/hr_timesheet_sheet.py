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
        context.update({'UpdateState':True})
        self.timesheet_ids.with_context(context).write({'state':'open'})
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
        self.timesheet_ids.write({'state':'draft'})
        return res
# -*- coding: utf-8 -*-
# Copyright 2018 Magnus ((www.magnus.nl).)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _, SUPERUSER_ID
from odoo.exceptions import UserError, ValidationError

class HrTimesheetSheet(models.Model):
    _inherit = "hr_timesheet_sheet.sheet"


    @api.one
    def action_timesheet_done(self):
        """
        On timesheet confirmed update analytic state to confirmed
        :return: Super
        """
        res = super(HrTimesheetSheet, self).action_timesheet_done()
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

    @api.one
    def action_timesheet_draft(self):
        """
        On timesheet reset draft check analytic shouldn't be in invoiced
        :return: Super
        """
        if any([ts.state == 'progress' for ts in self.timesheet_ids]):
        # if self.timesheet_ids.filtered('invoiced') or any([ts.state == 'progress' for ts in self.timesheet_ids]):
            raise UserError(_('You cannot modify timesheet entries either Invoiced or belongs to Analytic Invoiced!'))
        res = super(HrTimesheetSheet, self).action_timesheet_draft()
        if self.timesheet_ids:
            cond = '='
            rec = self.timesheet_ids.ids[0]
            if len(self.timesheet_ids) > 1:
                cond = 'IN'
                rec = tuple(self.timesheet_ids.ids)
            self.env.cr.execute("""
                            UPDATE account_analytic_line SET state = 'draft' WHERE id %s %s;
                            DELETE FROM account_analytic_line WHERE ref_id %s %s;
                    """ % (cond, rec, cond, rec))
            self.env.invalidate_all()
        return res
# -*- coding: utf-8 -*-
# Copyright 2018 Magnus ((www.magnus.nl).)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _, SUPERUSER_ID
from datetime import datetime, timedelta
from odoo.exceptions import UserError, ValidationError
from dateutil.rrule import (rrule)
from dateutil.relativedelta import relativedelta

class HrTimesheetSheet(models.Model):
    _inherit = "hr_timesheet_sheet.sheet"
    _order = "week_id desc"

    @api.multi
    @api.depends('end_mileage','business_mileage','starting_mileage')
    def _get_private_mileage_new(self):
        for sheet in self:
            m = sheet.end_mileage - sheet.business_mileage - sheet.starting_mileage
            sheet.private_mileage = m if m > 0 else 0
            
    private_mileage_new = fields.Integer(compute='_get_private_mileage_new', string='Private Mileage', store=True)

# -*- coding: utf-8 -*-
# Copyright 2018 Magnus ((www.magnus.nl).)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _

class Employee(models.Model):
    _inherit = "hr.employee"

    planning_week = fields.Boolean(string="Planning by week")
    timesheet_optional = fields.Boolean('Timesheet optional')
    timesheet_no_8_hours_day = fields.Boolean('Timesheet no 8 hours day')
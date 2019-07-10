# -*- coding: utf-8 -*-

from odoo import api, fields, models


class DateRange(models.Model):
    _inherit = "date.range"

    calender_name = fields.Char(string="Calender Name", translate=True)
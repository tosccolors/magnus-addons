# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class Department(models.Model):
    _inherit = "hr.department"

    cumm_overtime_cal = fields.Boolean(
        'Cumulative Overtime Balance',
        help="Show Cumulative Overtime Balance"
    )
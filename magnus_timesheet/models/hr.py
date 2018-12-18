# -*- coding: utf-8 -*-
# Copyright 2018 Magnus ((www.magnus.nl).)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _

class Employee(models.Model):
    _inherit = "hr.employee"

    planning_week = fields.Boolean(string="Planning by week")
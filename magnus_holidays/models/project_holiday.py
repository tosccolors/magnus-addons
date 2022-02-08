# -*- coding: utf-8 -*-
# Copyright 2018 Magnus ((www.magnus.nl).)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api

class Project(models.Model):
    _inherit = "project.project"

    holiday_consumption = fields.Boolean(string='Holiday Consumption')
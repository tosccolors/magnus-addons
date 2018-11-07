# -*- coding: utf-8 -*-
# Copyright 2018 Magnus ((www.magnus.nl).)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api

class Department(models.Model):
    _inherit = "hr.department"

    operating_unit_id = fields.Many2one('operating.unit', string='Operating Unit')
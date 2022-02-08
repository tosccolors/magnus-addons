# -*- coding: utf-8 -*-
# Copyright 2018 Magnus ((www.magnus.nl).)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, _

class Department(models.Model):
    _inherit = "hr.department"

    #manager_2_id = fields.Many2one('hr.employee', string='Co Manager')
    manager_2_ids = fields.Many2many('hr.employee', string='Co Manager')
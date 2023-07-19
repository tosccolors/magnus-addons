# -*- coding: utf-8 -*-
# Copyright 2018 Magnus ((www.magnus.nl).)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _

class User(models.Model):
    _inherit = "res.users"

    @api.multi
    @api.depends('employee_ids.klippa_user')
    def _get_employee_uses_klippa(self):
        for user in self:
            if user.employee_ids.filtered('klippa_user'):
                user.klippa_user = True
            else:
                user.klippa_user = False

    klippa_user = fields.Boolean(string="Employee uses Klippa", compute="_get_employee_uses_klippa", store=True)
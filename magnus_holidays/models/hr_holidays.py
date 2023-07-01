# -*- coding: utf-8 -*-
# Copyright 2018 Magnus ((www.magnus.nl).)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api

class Holidays(models.Model):
    _inherit = "hr.leave"

    state = fields.Selection(selection_add=[('written', 'Written')])

    # method not for v12
    # @api.model
    # def _check_leave_hours(self, leave_hours):
    #     return True

    #this approach not required due to allocation and leave object is differnt in V12
    # @api.depends('number_of_days', 'state')
    # def _compute_number_of_hours(self):
    #     for rec in self:
    #         rec.number_of_hours = 0.0
    #         if rec.state == 'validate':
    #             rec.number_of_hours = rec.number_of_days
    #             rec.virtual_hours = rec.number_of_days
    #         if rec.state == 'written':
    #             rec.number_of_hours = -rec.number_of_days
    #             rec.virtual_hours = -rec.number_of_days



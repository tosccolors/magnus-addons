# -*- coding: utf-8 -*-
# Copyright 2018 Magnus ((www.magnus.nl).)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api

class Holidays(models.Model):
    _inherit = "hr.holidays"

    state = fields.Selection(selection_add=[('written', 'Written')])

    @api.model
    def _check_leave_hours(self, leave_hours):
        return True

    @api.depends('number_of_hours_temp', 'state')
    def _compute_number_of_hours(self):
        for rec in self:
            rec.number_of_hours = 0.0
            if rec.state == 'validate' and rec.type == 'add':
                rec.number_of_hours = rec.number_of_hours_temp
                rec.virtual_hours = rec.number_of_hours_temp
            if rec.state == 'written' and rec.type == 'remove':
                rec.number_of_hours = -rec.number_of_hours_temp
                rec.virtual_hours = -rec.number_of_hours_temp


    @api.multi
    @api.onchange('employee_id')
    def onchange_partner_update_leave_hours(self):
        for rec in self:
            if rec.employee_id:
                rec.number_of_hours_temp = rec.employee_id.leave_hours

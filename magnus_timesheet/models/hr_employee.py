# -*- coding: utf-8 -*-
# Copyright 2018 Magnus ((www.magnus.nl).)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo.tools.translate import _

class Employee(models.Model):
    _inherit = "hr.employee"


    @api.one
    @api.depends('product_id')
    def _compute_fee_rate(self):
        if self.product_id:
            self.fee_rate = self.product_id.list_price

    @api.model
    def _get_category_domain(self):
        return [('categ_id','=', self.env.ref(
            'magnus_invoicing.product_category_fee_rate').id)]

    @api.one
    def _get_overtime_hours(self):
        self.overtime_hours = sum(
            self.env['hr_timesheet_sheet.sheet'].search([('employee_id', '=', self.id)]).mapped('overtime_hours'))

    planning_week = fields.Boolean(
        string="Planning by week"
    )
    timesheet_optional = fields.Boolean(
        'Timesheet optional'
    )
    timesheet_no_8_hours_day = fields.Boolean(
        'Timesheet no 8 hours day'
    )
    overtime_hours = fields.Float(
        compute="_get_overtime_hours",
        string='Overtime Hours'
    )
    product_id = fields.Many2one(
        'product.product',
        string='Fee Rate Product',
        domain=_get_category_domain
    )
    fee_rate = fields.Float(
        compute=_compute_fee_rate,
        string='Fee Rate',
        readonly=True
    )


class Department(models.Model):
    _inherit = "hr.department"


    operating_unit_id = fields.Many2one(
        comodel_name='operating.unit',
        string='Operating Unit',
        track_visibility='onchange'
    )
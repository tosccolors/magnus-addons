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

class ResUsers(models.Model):
    _inherit = "res.users"


    @api.multi
    def _get_operating_unit_id(self):
        """ Compute Operating Unit of Employee based on the OU in the 
        top Department."""
        employee_id = self._get_related_employees()
        assert len(employee_id) == 1, 'Only one employee can have this user_id'
        if employee_id.department_id:
            dep = self.env['hr.department'].search([('parent_id','=',False),('child_ids','in',
                                                [employee_id.department_id.id])])
        else:
            raise ValidationError(_('The Employee in the Analytic line has '
                                    'no department defined. Please complete'))
        return dep.operating_unit_id


class Department(models.Model):
    _inherit = "hr.department"


    operating_unit_id = fields.Many2one(
        comodel_name='operating.unit',
        string='Operating Unit',
        track_visibility='onchange'
    )
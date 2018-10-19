# -*- coding: utf-8 -*-
# Copyright 2018 Magnus ((www.magnus.nl).)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api


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


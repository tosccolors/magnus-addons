# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class Product(models.Model):
    _name = 'product.product'
    _inherit = ['product.product', 'data.track.thread']
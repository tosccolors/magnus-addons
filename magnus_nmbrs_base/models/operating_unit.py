from odoo import api, fields, models, tools, _


class OperatingUnit(models.Model):
    _inherit = 'operating.unit'

    nmbrs_id = fields.Char("nmbrs ID used for interface")

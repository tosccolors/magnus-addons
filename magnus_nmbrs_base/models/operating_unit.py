from odoo import api, fields, models, tools, _


class OperatingUnit(models.Model):
    """Adds possibility to save NMBRs database ID on the OU"""
    _inherit = 'operating.unit'

    nmbrs_id = fields.Char("nmbrs ID used for interface")

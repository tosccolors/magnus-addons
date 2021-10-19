from odoo import api, fields, models, _


class FiscalAdditionMapping(models.Model):
    """
    A table to store fiscal addition
    """
    _name = "fleet.fiscal.addition.mapping"
    _description = "model used to save fiscal addition mapping between NMBRs and Odoo"
    _rec_name = "fiscal_addition"

    fiscal_addition = fields.Char("Fiscal Addition")

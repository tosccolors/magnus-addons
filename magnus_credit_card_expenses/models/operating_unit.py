from odoo import api, fields, models, _


class OperatingUnit(models.Model):
    _inherit = 'operating.unit'

    creditcard_decl_journal_id = fields.Many2one('account.journal', 'Credit Card Expenses Journal',domain=['|',('type','=','bank'),('type','=','cash')])

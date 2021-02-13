from odoo import api, fields, models


class AccountAssetAsset(models.Model):
    _inherit = 'account.asset.asset'

    book_value = fields.Float(compute='_compute_book_value', method=True, digits=0, string='Book Value')

    @api.depends('salvage_value', 'value_residual')
    def _compute_book_value(self):
        self.book_value = self.salvage_value + self.value_residual
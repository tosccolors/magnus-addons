from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    @api.onchange('invoice_date', 'highest_name', 'company_id')
    def _onchange_invoice_date(self):
        # take care that onchange always sets accounting date to invoice date
        result = super()._onchange_invoice_date()
        if self.invoice_date and self.invoice_date != self.date:
            self.date = self.invoice_date
            self._onchange_currency()
        return result

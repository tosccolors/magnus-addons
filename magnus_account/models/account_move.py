from itertools import chain
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

    def _get_deferrable_lines(self):
        return chain(
            super()._get_deferrable_lines(),
            self.filtered(lambda account_move: account_move.move_type == "entry")
            .line_ids.filtered(lambda line: line.is_deferrable_line and not line.cutoff_source_id)
            .group_recordset_by(lambda move_line: move_line.move_id)
        )

from odoo import api, fields, models


class AccountBankStatement(models.Model):
    _inherit = "account.bank.statement"

    def write(self, vals):
        result = super().write(vals)
        if self.env.context.get(
                'account_statement_import_online_recalculate_ending_balance'
        ) and vals.get('line_ids'):
            self.with_context(
                account_statement_import_online_recalculate_ending_balance=False
            )._compute_ending_balance()
        return result

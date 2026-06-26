from odoo import api, fields, models


class OnlineBankStatementProvider(models.Model):
    _inherit = "online.bank.statement.provider"

    def _create_or_update_statement(
        self, data, statement_date_since, statement_date_until
    ):
        return super(
            OnlineBankStatementProvider,
            self.with_context(
                account_statement_import_online_recalculate_ending_balance=True
            )
        )._create_or_update_statement(data, statement_date_since, statement_date_until)

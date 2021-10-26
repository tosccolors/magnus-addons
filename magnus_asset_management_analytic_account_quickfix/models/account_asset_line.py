import datetime

from odoo import api, fields, models, _
from odoo.exceptions import UserError

class AccountAssetLine(models.Model):
    _inherit = 'account.asset.line'

    def _setup_move_line_data(self, depreciation_date, account, ml_type, move):
        res = super(AccountAssetLine, self)._setup_move_line_data(depreciation_date, account, ml_type, move)
        if ml_type == "expense":
            res["analytic_account_id"] = self.asset_id.analytic_account_id_2.id
        return res

from odoo import api, fields, models


class AccountAsset(models.Model):
    _inherit = 'account.asset'

    analytic_account_id_2 = fields.Many2one(
        comodel_name="account.analytic.account", string="Analytic Account",
    )

    @api.onchange('analytic_account_id_2')
    def onchange_analytic_account_id_2(self):
        self.account_analytic_id = self.analytic_account_id_2

    @api.model
    def create(self, vals):
        ctx = self._context
        if "create_asset_from_move_line" in ctx:
            analytic_account = self.env['account.analytic.account'].browse(vals["account_analytic_id"])
            vals['analytic_account_id_2'] = analytic_account.id
        return super(AccountAsset, self).create(vals)

from odoo import api, fields, models


class AccountAsset(models.Model):
    _inherit = 'account.asset'

    operating_unit_id = fields.Many2one(
        'operating.unit',
        'Operating Unit',
        default=lambda self: self.env['res.users'].operating_unit_default_get(self._uid)
    )

    @api.onchange('account_analytic_id')
    def onchange_analytic_account_id(self):
        if self.account_analytic_id.linked_operating_unit:
            self.operating_unit_id = self.account_analytic_id.operating_unit_ids.ids[0]
        else:
            self.operating_unit_id = False

    @api.model
    def create(self, vals):
        ctx = self._context
        if "create_asset_from_move_line" in ctx:
            analytic_account = self.env['account.analytic.account'].browse(vals["account_analytic_id"])
            vals['operating_unit_id'] = analytic_account.operating_unit_ids.id
        return super(AccountAsset, self).create(vals)

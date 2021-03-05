from odoo import fields, models


class AccountAssetProfile(models.Model):
    _inherit = 'account.asset.profile'

    has_equipments = fields.Boolean(string="This asset profile should generate equipments")

    equipment_category_id = fields.Many2one(
        comodel_name="maintenance.equipment.category",
        string="Equipment category",
        help="This category will be used for the created equipment when it "
             "is created automatically on validating a vendor bill that "
             "contains this asset category.",
    )


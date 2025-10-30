from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    general_cutoff_journal_id = fields.Many2one(
        related="company_id.general_cutoff_journal_id",
        readonly=False,
    )

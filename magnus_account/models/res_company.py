from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    general_cutoff_journal_id = fields.Many2one(
        "account.journal",
        string="Cut-off Misc Journal",
        check_company=True,
    )

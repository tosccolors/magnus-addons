from odoo import fields, models


class PsTimeLine(models.Model):
    _inherit = "ps.time.line"

    office_day_hub = fields.Integer()
    office_day_hub_boolean = fields.Boolean(
        string="Office Day Hub",
        compute="_compute_office_day_hub_boolean",
        inverse="_inverse_office_day_hub_boolean",
    )

    def _compute_office_day_hub_boolean(self):
        for this in self:
            this.office_day_hub_boolean = bool(this.office_day_hub)

    def _inverse_office_day_hub_boolean(self):
        for this in self:
            this.office_day_hub = 1 if this.office_day_hub_boolean else 0

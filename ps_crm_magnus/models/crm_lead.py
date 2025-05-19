# Copyright 2025 The Open Source Company (www.tosc.nl).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models
from odoo.addons.ps_planning.models.ps_contracted_line import _get_work_days_dates


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    date_deadline = fields.Date("Deadline submission")

    def _date_diff_days(self, date_start, date_end):
        """
        Use work days instead of calendar days
        """
        return _get_work_days_dates(date_start, date_end)

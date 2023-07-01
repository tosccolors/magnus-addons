# -*- coding: utf-8 -*-
# Copyright 2017 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models


class ResCompany(models.Model):

    _inherit = 'res.company'

    def find_daterange_cw(self, date_str):
        self.ensure_one()
        cw_id = self.env.ref('magnus_date_range_week.date_range_calender_week')
        return self.env['date.range'].search([
            ('type_id', '=', cw_id.id),
            ('date_start', '<=', date_str),
            ('date_end', '>=', date_str),
            '|',
            ('company_id', '=', self.id),
            ('company_id', '=', False),
        ], limit=1, order='company_id asc')

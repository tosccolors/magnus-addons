# -*- coding: utf-8 -*-
# Copyright 2018 Magnus ((www.magnus.nl).)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api

class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    operating_unit_id = fields.Many2one('operating.unit',
                                        related='project_id.operating_unit_id',
                                        string='Operating Unit', store=True,
                                        readonly=True)
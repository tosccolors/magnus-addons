# -*- coding: utf-8 -*-
# Copyright 2009-2018 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _

class AccountAssetRemove(models.TransientModel):
    _inherit = 'account.asset.remove'

    def _get_removal_data(self, asset, residual_value):
        move_lines = super(AccountAssetRemove, self)._get_removal_data(asset, residual_value)
        if not asset.operating_unit_id:
            return move_lines
        operating_unit_id = asset.operating_unit_id.id
        for ml in move_lines:
            ml[2].update({'operating_unit_id':operating_unit_id})
        return move_lines


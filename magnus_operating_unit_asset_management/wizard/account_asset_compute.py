# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#
#    Copyright (C) 2010-2012 OpenERP s.a. (<http://openerp.com>).
#    Copyright (c) 2014 Noviat nv/sa (www.noviat.com). All rights reserved.
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program. If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp.osv import fields, orm
from openerp.tools.translate import _


class AccountAssetCompute(models.TransientModel):
    _inherit = 'account.asset.compute'
    operating_unit_id = fields.Many2one('operating.unit', string='Operating Unit', required=False)

    
    
    # Overridden:
    def asset_compute(self):
        domain = [("state", "=", "open")]
        if self.operating_unit_id:
            domain += [('operating_unit_id', '=', self.operating_unit_id.id)]

        assets = self.env["account.asset"].search(domain)
        created_move_ids, error_log = assets._compute_entries(
            self.date_end, check_triggers=True
        )

        if error_log:
            module = __name__.split("addons.")[1].split(".")[0]
            result_view = self.env.ref(
                "{}.{}_view_form_result".format(module, self._table)
            )
            self.note = _("Compute Assets errors") + ":\n" + error_log
            return {
                "name": _("Compute Assets result"),
                "res_id": self.id,
                "view_mode": "form",
                "res_model": "account.asset.compute",
                "view_id": result_view.id,
                "target": "new",
                "type": "ir.actions.act_window",
                "context": {"asset_move_ids": created_move_ids},
            }

        return {
            "name": _("Created Asset Moves"),
            "view_mode": "tree,form",
            "res_model": "account.move",
            "view_id": False,
            "domain": [("id", "in", created_move_ids)],
            "type": "ir.actions.act_window",
        }


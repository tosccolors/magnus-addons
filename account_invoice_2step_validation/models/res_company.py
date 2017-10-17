# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright 2014 BAS Solutions
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from odoo import models, fields, api, _
import odoo.addons.decimal_precision as dp

class Company(models.Model):
    _inherit = 'res.company'

    verify_setting = fields.Float('Invoice Amount bigger than', digits=dp.get_precision('Account'))


    @api.multi
    def write(self, vals):
        res = super(Company, self).write(vals)

        # -- deep
        # Functionality for updating "verif_tresh_exceeded" are split b/w Company & Invoice Object

        if 'verify_setting' in vals:
            for case in self:
                treshold = case.verify_setting

                self._cr.execute("""
                        UPDATE account_invoice
                        SET verif_tresh_exceeded=True
                        WHERE amount_untaxed > %s
                        AND company_id= %s
                        AND type='in_invoice'
                        AND state!='paid';

                        UPDATE account_invoice
                        SET verif_tresh_exceeded=False
                        WHERE amount_untaxed <= %s
                        AND company_id= %s
                        AND type='in_invoice'
                        AND state!='paid'
                        """, ( treshold, case.id, treshold, case.id,))

        return res



# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

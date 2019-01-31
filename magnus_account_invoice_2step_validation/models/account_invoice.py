# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2013 Eurogroup Consulting NL (<http://eurogroupconsulting.nl>).
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

class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    def _get_current_user(self):
        grp_ver = self.env.user.has_group('account_invoice_2step_validation.verification')
        grp_auth = self.env.user.has_group('account_invoice_2step_validation.authorize')
        for line in self:
            line.current_user_verify = grp_ver
            line.current_user_auth = grp_auth
            if line.user_id.id == self.env.user.id:
                line.current_user_verify = False
            else:
                line.current_user_auth = False

    current_user_verify = fields.Boolean('Current User Verify', compute=_get_current_user)
    current_user_auth = fields.Boolean('Current User Auth.', compute=_get_current_user)


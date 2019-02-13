# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright 2016 BAS Solutions
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

from odoo import fields, models, api


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    invoice_description = fields.Text('Description')

    @api.multi
    def invoice_print(self):
        """ Print the invoice and mark it as sent, so that we can see more
            easily the next step of the workflow
        """
        self.ensure_one()
        self.sent = True
        return self.env['report'].get_action(self, 'account.invoice.custom')

    @api.multi
    def group_by_analytic_acc(self):
        self.ensure_one()
        result = {}
        for line in self.invoice_line_ids:
            if line.account_analytic_id in result:
                result[line.account_analytic_id].append(line)
            else:
                result[line.account_analytic_id] = [line]
        return result

class ResCompany(models.Model):
    _inherit = 'res.company'

    report_background_image = fields.Binary(
            'Background Image for Report',
            help='Set Background Image for Report')


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

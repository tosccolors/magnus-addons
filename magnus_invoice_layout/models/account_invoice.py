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

    
    def invoice_print(self):
        """ Print the invoice and mark it as sent, so that we can see more
            easily the next step of the workflow
        """
        self.ensure_one()
        self.sent = True
        return self.env['report'].get_action(self, 'account.invoice.custom')

#    def invoice_print(self, cr, uid, ids, context=None):
#        '''
#        This function prints the invoice and mark it as sent, so that we can see more easily the next step of the workflow
#        '''
#        assert len(ids) == 1, 'This option should only be used for a single id at a time.'
#        self.write(cr, uid, ids, {'sent': True}, context=context)
#        datas = {
#            'ids': ids,
#            'model': 'account.invoice.custom',
#            'form': self.read(cr, uid, ids[0], context=context)
#        }
#        return {
#            'type': 'ir.actions.report.xml',
#            'report_name': 'account.invoice.custom',
#            'datas': datas,
#            'nodestroy': True
#        }

class ResCompany(models.Model):
    _inherit = 'res.company'

    report_background_image = fields.Binary(
            'Background Image for Report',
            help='Set Background Image for Report')


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

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

from openerp.osv import osv, fields


class account_invoice(osv.osv):
    _inherit = 'account.invoice'

    _columns = {
        'invoice_description': fields.text('Description'),

    }

    def invoice_print(self, cr, uid, ids, context=None):
        '''
        This function prints the invoice and mark it as sent, so that we can see more easily the next step of the workflow
        '''
        assert len(ids) == 1, 'This option should only be used for a single id at a time.'
        self.write(cr, uid, ids, {'sent': True}, context=context)
        datas = {
            'ids': ids,
            'model': 'account.invoice.custom',
            'form': self.read(cr, uid, ids[0], context=context)
        }
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'account.invoice.custom',
            'datas': datas,
            'nodestroy': True
        }

account_invoice()


class res_company(osv.osv):
    _inherit = 'res.company'

    _columns = {
        'report_background_image': fields.binary(
            'Background Image for Report',
            help='Set Background Image for Report'),
    }

res_company()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

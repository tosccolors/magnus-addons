# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2013-Today OpenERP SA (<http://www.openerp.com>) and Magnus W. Hulshof
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>
#
##############################################################################
{
    'name': 'Inter Company Module for Invoices',
    'version': '7.0.1.1.0',
    'description': ''' Module for synchronization of Invoices between
     several companies. For example, this allows you to have a Customer Invoice created
    automatically when a Supplier Invoice is validated with another
     company of the system as supplier, and inversely.

    Supported documents are invoices/refunds.
''',
    'author': 'OpenERP SA/ Magnus',
    'website': 'http://www.magnus.nl',
    'license': 'AGPL-3',
    'depends': [
        'account',
        'multi_company',
        ],
    'data': [
        'views/inter_company_so_po_view.xml',
    ],
    'test': [
    ],
    'demo': [],
    'installable': True,
    'auto_install': False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

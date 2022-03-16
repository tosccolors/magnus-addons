# -*- encoding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2013 Megis - Willem Hulshof - www.megis.nl
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsability of assessing all potential
# consequences resulting from its eventual inadequacies and bugs.
# End users who are looking for a ready-to-use solution with commercial
# garantees and support are strongly adviced to contract a Free Software
# Service Company like Veritos.
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA
#
##############################################################################

{
    'name'       : 'Magnus Follow Up',
    'version'    : '0.1',
    'category'   : 'accounts',
    'description': """
This module adds customization for Magnus, like :\n
- custom credit control per company, including invoices in appendix\n
- open invoice status, showing latest status per open invoice for manual follow up\n
    """,
    'author'  : 'Magnus - Willem Hulshof, D. Prosee',
    'website' : 'http://www.magnus.nl',
    'depends' : ['account_credit_control','account'
    ],
    'data' : [
            "views/open_invoice_status_view.xml",

    ],
    'demo' : [],
    'installable': True
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:


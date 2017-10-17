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
    'name' : 'account_invoice_2step_validation',
    'version' : '0.9',
    'category': 'accounts',
    'description': """
This module adds authorization steps in workflow in supplier invoices.
=============================================================================

Enchanced to add
* Authorization
* Verification status on the Invoice

    """,
    'author'  : 'Eurogroup Consulting - Willem Hulshof',
    'website' : 'http://www.eurogroupconsulting.nl',
    'depends' : ['account',
		'account_cancel',
		'account_voucher',
        "account_payment_order", # -- added: deep
        "project",
        "publishing_accounts"
    ],
    'data' : ["security/account_security.xml",
	          "views/res_company_view.xml",
              "views/account_view.xml",
	          "views/account_invoice_view.xml",
              "wizard/wizard_view.xml",
              "security/ir.model.access.csv",
    ],
    'demo' : [],
    'installable': True
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:


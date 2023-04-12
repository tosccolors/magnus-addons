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
    'name' : 'Magnus Credit Card Expenses',
    'version' : '1.0',
    'category': 'other',
    'description': """
Enhances the Hr Expenses Module
=============================================================================
This module adds "department_id.manager_id" to expense domain hr_user and
adapts the workflow and tax processing. Also a special credit card declaration journal is
defined. This is used for reconciliation of the expenses and the final expense invoice.


    """,
    'author'  : 'TOSC - SB',
    'website' : 'http://www.tosc.nl',
    'depends' : ['magnus_expense'],
    'data'    : [
        'security/hr_expense_security.xml',
        'security/ir.model.access.csv',
        'security/ir_rule.xml',
        'views/company_view.xml',
        'views/hr_expense_views.xml',
        'views/menu_view.xml',
        ],
    'demo' : [],
    'installable': True
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:


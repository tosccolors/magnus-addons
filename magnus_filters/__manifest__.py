# -*- coding: utf-8 -*-
# Copyright 2018 Willem Hulshof Magnus (www.magnus.nl).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    'name': "magnus_filters",

    'summary': """
        This module creates some filters in magnus' modules """,

    'description': """
        This module creates some filters in magnus' modules. 
    """,

    'author': "TOSC",
    'website': "http://www.tosc.nl",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'module_category_specific_industry_applications',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': [
                'magnus_timesheet'
                ],

    # always loaded
    'data': [
        'views/account_analytic_view.xml',
        'views/analytic_invoice.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
#        'demo/demo.xml',
    ],
}
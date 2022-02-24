# -*- coding: utf-8 -*-
# Copyright 2018 Willem Hulshof Magnus (www.magnus.nl).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    'name': "Magnus CRM",

    'summary': "Opportunities - Extended",

    'description': """
This module creates monthly revenue forecast lines.
===================================================

For each calendar month between the start date and end date, a month-revenue is generated.
Go to Reports>Monthly Revenue to see the overview of the expected revenue per month derived from all the opportunities.

Steps to generate monthly expected revenue:
--------------------------------------------------
* Expected revenue should be filled. Once set the monthly expected revenue fields will be visible.
* Then you can fill start date and end date to get splitted revenues per month.
    """,

    'author': "Magnus",
    'website': "http://www.magnus.nl",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Sales',
    'version': '0.1',

    # any module necessary for this one to work correctly
    # 'depends': ['base', 'crm', 'crm_sector', 'project', 'operating_unit', 'hr', 'web_readonly_bypass','utm', 'date_range','web_notify'],
    # commented by deekshith
    'depends': ['base','uom', 'crm', 'crm_industry', 'project', 'operating_unit', 'hr','utm', 'date_range','web_notify','sale'],

    # always loaded
    'data': [
        'security/crm_security.xml',
        'security/ir.model.access.csv',
        'views/crm_lead_views.xml',
        # 'views/crm_menus.xml',
    ],
    'installable': True,
    # only loaded in demonstration mode
    'demo': [
        # 'demo/demo.xml'
    ],
}
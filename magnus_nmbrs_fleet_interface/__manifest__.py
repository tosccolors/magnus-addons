# -*- coding: utf-8 -*-
{
    'name': "Magnus NMBRs Fleet Interface",

    'summary': """
        Provides an interface push fleet changes from Odoo to NMBRs """,

    'author': "Magnus - Hayo Bos",
    'website': "http://www.magnus.nl",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Payroll',
    'version': '1.0',
    'installable': True,
    # any module necessary for this one to work correctly
    'depends': ['magnus_fleet_rdw'],

    # always loaded
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/nmbrs_fleet_view.xml',
        'wizard/nmbrs_fleet_wizard.xml',
        'views/template_view.xml'
    ],
    # only loaded in demonstration mode
    'demo': [
        # 'demo/demo.xml',
    ],
    'qweb': [
        "static/src/xml/qweb.xml",
    ],
}
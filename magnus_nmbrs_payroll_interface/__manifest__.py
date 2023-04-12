# -*- coding: utf-8 -*-
{
    'name': "Magnus NMBRs Payroll Interface",

    'summary': """
        Provides an interface to load journal entries directly from NMBRs into Odoo""",

    'author': "TOSC - Hayo Bos",
    'website': "http://www.tosc.nl",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Payroll',
    'version': '1.0',
    'installable': True,
    # any module necessary for this one to work correctly
    'depends': ['magnus_nmbrs_base', 'analytic', 'account'],

    # always loaded
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/payroll_view.xml',
        'wizard/nmbrs_payroll_run_wizard.xml',
        'views/template_view.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        # 'demo/demo.xml',
    ],
    'qweb': [
        "static/src/xml/qweb.xml",
    ],
}
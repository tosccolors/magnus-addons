# -*- coding: utf-8 -*-
{
    'name': "Magnus NMBRs Employee Interface",

    'summary': """
        Provides the NMBRs Employee Interface """,
    'author': "TOSC - Hayo Bos",
    'website': "http://www.tosc.nl",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Payroll',
    'version': '1.0',
    'installable': True,
    # any module necessary for this one to work correctly
    'depends': ['operating_unit', 'magnus_hr', 'magnus_nmbrs_base'],

    # always loaded
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/hr_views.xml',
        'wizard/hr_employee_wizard_view.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        # 'demo/demo.xml',
    ],
    'qweb': [
        # "static/src/xml/qweb.xml",
    ],
}
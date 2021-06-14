# -*- coding: utf-8 -*-
{
    'name': "Magnus NMBRs Employee Interface",

    'summary': """
        Provides the NMBRs Employee Interface """,

    'description': """
        Provides configuration menu for interfaces between Odoo and NMBRs
    """,

    'author': "Magnus - Hayo Bos",
    'website': "http://www.magnus.nl",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Report',
    'version': '0.3',
    'installable': True,
    # any module necessary for this one to work correctly
    'depends': ['operating_unit', 'magnus_hr'],

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
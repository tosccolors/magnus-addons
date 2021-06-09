# -*- coding: utf-8 -*-
{
    'name': "Magnus NMBRs Base Module",

    'summary': """
        Provides the base for the NMBRs interfaces. This module is no interface itself.""",

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
    'depends': ['operating_unit'],

    # always loaded
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/api_config_view.xml',
        'views/operating_unit_view.xml',
        'views/nmbrs_analytic_account_mapping_view.xml',
        'wizard/nmbrs_analytic_account_wizard.xml',
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
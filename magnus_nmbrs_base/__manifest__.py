# -*- coding: utf-8 -*-
{
    'name': "Magnus NMBRs Base Module",

    'summary': """
        Provides the base for the NMBRs interfaces. This module is no interface itself.""",

    'description': """
        This module provides the base module for the interfaces between Odoo and NMBRs. All NMBRs interfaces depend on 
        module, as it provides the underlying, shared functionalities for the separate interfaces. 
        Included: 
        - A configuration view (top ribbon --> NMBRS), where an authorised user can provide her / his username and API token
        - A mapping table to map analytic accounts between NMBRs and Odoo 
        - Addition of an ID field on the operating unit object
        - Security: a group category to which new groups can be added, and basic authorisations for the configuration menu
    """,

    'author': "Magnus - Hayo Bos",
    'website': "http://www.magnus.nl",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Payroll',
    'version': '1.0',
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
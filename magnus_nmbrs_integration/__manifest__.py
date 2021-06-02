# -*- coding: utf-8 -*-
{
    'name': "Magnus NMBRS Integration",

    'summary': """
        Provides an integration between NMBRS and Odoo""",

    'description': """
        Provides an integration between NMBRS and Odoo
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
    'depends': ['operating_unit', 'magnus_hr', 'magnus_fleet'],

    # always loaded
    'data': [
        'views/api_config_view.xml',
        'views/operating_unit_view.xml',
        'views/hr_views.xml',
        'views/payroll_view.xml',
        'views/nmbrs_fleet_view.xml',
        'wizard/hr_employee_wizard_view.xml',
        'wizard/nmbrs_analytic_account_wizard.xml',
        'wizard/nmbrs_payroll_run_wizard.xml',
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
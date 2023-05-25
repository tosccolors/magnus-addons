# -*- coding: utf-8 -*-
{
    'name': "magnus_landing_page",

    'summary': """
        Employee Landing Page""",

    'description': """
        Employee Landing Page
    """,

    'author': "TOSC",
    'website': "http://www.tosc.nl",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Report',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['magnus_timesheet', 'magnus_holidays','magnus_expense'],

    # always loaded
    'data': [
        'security/magnus_security.xml',
        'security/ir.model.access.csv',
        'views/hr_employee_landing_page_views.xml',
        'views/hr_holidays_views.xml',
        'views/analytic_views.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        # 'demo/demo.xml',
    ],
}
# -*- coding: utf-8 -*-
{
    'name': "magnus_expense",

    'summary': """
        Adjustments to Expense Module
        """,

    'description': """
    """,

    'author': "TOSC",
    'website': "http://www.tosc.nl",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Human Resources',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['hr_expense', 'hr_expense_operating_unit', 'invoice_line_revenue_distribution_operating_unit'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'security/security.xml',
        'views/hr_expense_views.xml',
        'views/res_company_view.xml',
        'views/analytic_views.xml',
        # 'views/account_views.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        # 'demo/demo.xml',
    ],
}
# -*- coding: utf-8 -*-
{
    'name': "magnus_security",

    'summary': """
        Magnus Security""",

    'description': """
        Magnus Security
    """,

    'author': "Magnus",
    'website': "http://www.magnus.nl",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Human Resources',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['magnus_timesheet','hr_holidays', 'web_tree_many2one_clickable'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/hr_views.xml',
        'views/analytic_views.xml',
        # 'views/hr_timesheet_views.xml',
        'views/hr_timesheet_assets.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        # 'demo/demo.xml',
    ],
}
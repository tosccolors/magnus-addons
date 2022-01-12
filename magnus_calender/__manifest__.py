# -*- coding: utf-8 -*-
{
    'name': "Magnus Calender",

    'summary': """
        Magnus Calender""",

    'description': """
        Magnus Calender
    """,

    'author': "Magnus",
    'website': "http://www.magnus.nl",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['account_fiscal_month','account_fiscal_year'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/date_range_views.xml',
        # 'views/templates.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        # 'demo/demo.xml',
    ],
    'post_init_hook': 'post_init_hook',
}


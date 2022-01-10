# -*- coding: utf-8 -*-
{
    'name': "magnus_operating_unit_asset_management",

    'summary': """
        Adds OU to OCA Asset Management module""",

    'description': """
        Adds OU to OCA Asset Management module
    """,

    'author': "Magnus - Hayo Bos",
    'website': "http://www.magnus.nl",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Report',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['account_asset_management', 'operating_unit'],

    # always loaded
    'data': [
        'views/account_asset_views.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        # 'demo/demo.xml',
    ],
}
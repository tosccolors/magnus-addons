# -*- coding: utf-8 -*-
{
    'name': "magnus_asset_management_analytic_account_quickfix",

    'summary': """
        Solves analytic account issue with the asset module""",

    'description': """
        Solves analytic account issue with the asset module
    """,

    'author': "Magnus - Hayo Bos",
    'website': "http://www.magnus.nl",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Report',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['magnus_operating_unit_asset_management', 'magnus_assets_equipment_link'],

    # always loaded
    'data': [
        'views/account_asset_views.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        # 'demo/demo.xml',
    ],
}
# -*- coding: utf-8 -*-
{
    'name': "magnus_asset_management_analytic_account_quickfix",

    'summary': """
        Solves analytic account issue with the asset module""",

    'description': """
        Solves analytic account issue with the asset module, do not install when migrating to 12!! 
        Set account_asset.account_analytic = account_asset.analytic_account_2 when this module was installed on Odoo 10. 
    """,

    'author': "TOSC - Hayo Bos",
    'website': "http://www.tosc.nl",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Report',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['magnus_assets_equipment_link'],

    # always loaded
    'data': [
        'views/account_asset_views.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        # 'demo/demo.xml',
    ],
}
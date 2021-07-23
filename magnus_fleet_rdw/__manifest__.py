# -*- coding: utf-8 -*-
{
    'name': "Magnus Fleet RDW",

    'summary': """
        Provides a simple interface to fetch RDW data using the RDW API """,

    'author': "Magnus - Hayo Bos",
    'website': "http://www.magnus.nl",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Report',
    'version': '1.0',
    'installable': True,
    # any module necessary for this one to work correctly
    'depends': ['magnus_fleet'],

    # always loaded
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/fleet_view.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        # 'demo/demo.xml',
    ],
    'qweb': [
        # "static/src/xml/qweb.xml",
    ],
}
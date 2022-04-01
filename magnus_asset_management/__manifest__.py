# -*- coding: utf-8 -*-
# Copyright 2009-2018 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Magnus Assets Management',
    'version': '10.0.0.0.0',
    'license': 'AGPL-3',
    'depends': [
        'account_asset_management', 'magnus_operating_unit_asset_management'
    ],
    'conflicts': ['account_asset'],
    'author': "Magnus",
    'website' : "https://www.magnus.nl/",
    'category': 'Accounting & Finance',
    'sequence': 33,
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',

        'reports/asset_report_view.xml',
    ],
    'auto_install': False,
    'installable': True,
    'application': False,
}

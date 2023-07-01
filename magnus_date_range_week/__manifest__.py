# -*- coding: utf-8 -*-
# Copyright 2017 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Magnus Calender Week',
    'summary': """
        Provide a calender week date range type""",
    'version': '10.0.1.0.0',
    'license': 'AGPL-3',
    'author': 'TOSC, Odoo Community Association (OCA)',
    'website': 'https://www.magnus.nl',
    'depends': [
        'date_range','account_fiscal_year'
    ],
    'data': [
        'data/date_range_type.xml',
        'views/date_range_type.xml',
    ],
}

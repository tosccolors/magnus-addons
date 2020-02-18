# -*- coding: utf-8 -*-
# Copyright 2017 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Magnus Fleet',
    'summary': """
        Changes in contract notifications and new fields""",
    'version': '10.0.1.0.0',
    'license': 'AGPL-3',
    'author': 'Magnus, Odoo Community Association (OCA)',
    'website': 'https://www.magnus.nl',
    'depends': [
        'fleet',
        'magnus_timesheet'
    ],
    'data': [
        'views/fleet_view.xml',
    ],
}

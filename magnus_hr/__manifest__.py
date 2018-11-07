# -*- coding: utf-8 -*-
# Copyright 2018 Willem Hulshof Magnus (www.magnus.nl).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    'name': 'Magnus Employee Directory',

    'summary': "Departments - extended",

    'description': """
Human Resources Management
==========================

This module adds Operating Unit field in hr.department object.
""",

    'author': "Magnus",
    'website': "http://www.magnus.nl",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Human Resources',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'hr', 'operating_unit'],

    # always loaded
    'data': [
        'views/hr_views.xml',
    ],
    'installable': True,
    # only loaded in demonstration mode
    'demo' : [],
}
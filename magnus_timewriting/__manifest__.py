# -*- coding: utf-8 -*-
# Copyright 2018 Willem Hulshof Magnus (www.magnus.nl).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    'name': 'Magnus Timewriting',

    'summary': "Timesheets - extended",

    'description': """
Timesheets - extended
=====================
This module adds a button 'Duplicate last week' in Summary tab of Timesheet form.
While pressing this button it duplicates the timesheet's projects and tasks (without the hours) of last week to the current week.
""",

    'author': "Magnus",
    'website': "http://www.magnus.nl",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Human Resources',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'hr_timesheet', 'magnus_timesheet', 'hr_timesheet_task'],

    # always loaded
    'data': [
        'views/hr_timesheet_views.xml',
    ],
    'installable': True,
    # only loaded in demonstration mode
    'demo' : [],
}
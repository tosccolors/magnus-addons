# -*- coding: utf-8 -*-
# Copyright 2018 Willem Hulshof Magnus (www.magnus.nl).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    'name': "magnus_project",

    'summary': "Projects - extended",

    'description': """
        This module creates a many2one field operating_unit_id in project.project and account.analytic.line. \n
        The operating unit defined in the project.project is copied to each timesheet_ids(account.analytic.line) created for this project.
    """,

    'author': "TOSC",
    'website': "http://www.tosc.nl",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Project',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['project',
                'operating_unit',
                'analytic',
                'hr_timesheet_sheet'],

    # always loaded
    'data': [
        'security/magnus_security.xml',
        'security/ir.model.access.csv',
        'views/project_views.xml',
        'views/hr_timesheet_views.xml',
        'views/menuitem.xml',
        # 'report/report_invoice.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        # 'demo/demo.xml',
    ],
}
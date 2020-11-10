# -*- coding: utf-8 -*-
# Copyright 2018 Willem Hulshof Magnus (www.magnus.nl).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    'name': "Magnus Leave Management",

    'summary': """
        Leave Management - extended
    """,

    'description': """
        This module adds a boolean field in the object project.project, named 'Holiday Consumption'. \nWhen this boolean is TRUE for a certain project.project and a user write time in the hr_timesheet_sheet.sheet and this time record has the status "Approved" on the project.project it should not only make a line in the object account.analytic.line but also a  new record in the object hr.holidays.
    """,

    'author': "Magnus",
    'website': "http://www.magnus.nl",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Human Resources',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'project', 'hr_timesheet', 'hr_timesheet_sheet', 'hr_holidays', 'hr_holidays_hour', 'hr_holidays_validity_date', 'magnus_timesheet'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/project_holiday_views.xml',
        'views/hr_holiday_status_view.xml',
        # 'views/templates.xml',
    ],
    # only loaded in demonstration mode
    'installable': True,
    'demo': [
        # 'demo/demo.xml',
    ],
}

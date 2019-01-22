# -*- coding: utf-8 -*-
# Copyright 2018 Willem Hulshof Magnus (www.magnus.nl).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    'name': 'Magnus Timesheet',

    'summary': "Timesheets, Activities, Date Ranges",

    'description': """
        Record and validate timesheets and attendances easily - extended
==============================================================================

The extended timesheet validation process is:
--------------------------------------------------
* Timesheet period is set to weeks (from Monday to Sunday).
* Each week day (Monday-Friday) needs to have at least 8 logged hours.
* Each Monday-Friday period needs to have at least 40 logged hours.
* Logged hours should be 0 - 24.

The extended date range validation process is:
--------------------------------------------------
* Name is prepended with year generated according to ISO 8601 Calendar.
* Name is appended with week number generated according to ISO 8601 Calendar.
* Note: Start date should be Monday while generating weekly date ranges for timesheet. Also a date range must be unique per company""",

    'author': "Magnus",
    'website': "http://www.magnus.nl",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Human Resources',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['hr_timesheet_task',
                'magnus_invoicing',
                'fleet',
                'magnus_date_range_week',
                'product_uom_unece',
                'magnus_project',
                'web_m2x_options',
                'web_readonly_bypass',
                'sale_timesheet'],

    # always loaded
    'data': [
        'security/magnus_security.xml',
        'report/hr_chargeability_report.xml',
        'views/hr_timesheet_view.xml',
        'views/project_timesheet_view.xml',
        'views/project_view.xml',
        'views/analytic_account_view.xml',
        'views/hr_timesheet_assets.xml',
        'views/hr_view.xml',
        'views/analytic_view.xml',
        'views/fleet_view.xml',
    ],
    'installable': True,
    # only loaded in demonstration mode
    'demo' : [],
}
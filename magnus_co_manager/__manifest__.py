# -*- coding: utf-8 -*-

{
    'name': 'Magnus - Co Manager for Departments',
    'version': '1.0',
    'author'  : 'Magnus - Hayo Bos',
    'website' : 'http://www.magnus.nl',
    'category': 'Human Resources',
    'description': """Adds a co-manager field to a department""",
    'depends': ['magnus_expense', 'magnus_timesheet'],
    'summary': 'Employee,Department',
    'data': [
        'security/ir_rule.xml',
        'views/hr_views.xml',
    ],

    'installable': True,
    'application': True,
}

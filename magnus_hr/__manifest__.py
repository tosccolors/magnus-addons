# -*- coding: utf-8 -*-
# Copyright 2018 Willem Hulshof Magnus (www.magnus.nl).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    'name': 'Magnus Employee Directory',

    'summary': "HRM - extended",

    'description': """
Human Resources Management - extended
=====================================

This module adds the following fields:\n
In the object hr.employee on the tab 'HR Settings' under the heading 'Duration of Service' creates three new date fields called: 'Official Date of Employment', 'Temporary Contract' and 'End Date of Employment'. These first two date fields do not affect the 'lengt_of_service' field, the end-date-of-employment stops the counting of the length of service from the 'initial_employment_date'.\n
In the object hr.employee on the tab 'Public Information' under the heading 'Position' creates a new boolean called 'External'. If the boolean is set to true a new character field called 'Supplier' becomes visible.\n
In the object hr.employee on the tab 'Public Information' under the heading 'Position' creates a new m2o selection field of hr.employee called 'Mentor' similar to Manager (parent_id) and Coach (coach_id).\n
In the object hr.employee on the tab 'HR Settings' under the heading 'Leaves' creates two new integer fields called 'Parttime' and 'Allocated Leaves'.\n
In the object hr.employee on the tab 'Personal Information' under the heading 'Contact Information' creates a new character field called 'Emergency Contact'.\n
In the object hr.employee creates a new tab called 'Description' and on this tab creates a new text field called 'Description'.\n
In the object hr. employee on the tab 'HR Settings' under the heading 'Status' creates a new character field called 'Pass Number Alarm'.
""",

    'author': "Magnus",
    'website': "http://www.magnus.nl",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Human Resources',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'hr', 
    # 'hr_employee_seniority', commented coz the source module not found
    'hr_employee_service',
     'hr_contract'],

    # always loaded
    'data': [
        'views/hr_views.xml',
        'wizard/hr_employee_wizard_view.xml',
        'views/template_view.xml', 
        
    ],
    
    'installable': True,
    # only loaded in demonstration mode
    'demo' : [],
        'qweb': [
        "static/src/xml/qweb.xml",
    ],
}
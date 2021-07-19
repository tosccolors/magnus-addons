# -*- coding: utf-8 -*-
{
    'name': "Magnus NMBRs Employee Interface",

    'summary': """
        Provides the NMBRs Employee Interface """,

    'description': """
        This module provides an employee interface between Odoo and NMBRs. When using this module, an option on the 
        employee wizard is added such that the created employee is created in NMBRs as well, preserving the employee number
        on both sides. In this version, only the creation of employees is supported. Changes in employee data should still
        be taken care of manually on both sides. 
        Features:
        -A Boolean on employee wizard that asks for insertion of the employee in NMBRs. If the user ticks the box, several
        fields appear needed for the employee creation in NMBRs. Note that the data sent to NMBRs consists of those fields as well
        as other fields of the wizard (bank account, email, ..). 
        -Technically, the employee will be created in Odoo first. Subsequently, the employee is created in NMBRs and then the
        ID that NMBRs returns is saved on the employee in Odoo as well, to provide future communications between NMBRs and Odoo.
        -A mapping table to map nationalities from Odoo to NMBRs
        -Security on the nationality mapping table
    """,

    'author': "Magnus - Hayo Bos",
    'website': "http://www.magnus.nl",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Payroll',
    'version': '1.0',
    'installable': True,
    # any module necessary for this one to work correctly
    'depends': ['operating_unit', 'magnus_hr', 'magnus_nmbrs_base'],

    # always loaded
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/hr_views.xml',
        'wizard/hr_employee_wizard_view.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        # 'demo/demo.xml',
    ],
    'qweb': [
        # "static/src/xml/qweb.xml",
    ],
}
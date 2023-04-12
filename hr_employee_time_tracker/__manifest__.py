# -*- coding: utf-8 -*-
{
    'name': "hr_employee_time_tracker",

    'summary': """
            Employee time tracker
    """,

    'description': """

    """,

        'author': "TOSC - Willem Hulshof",
        'website': "http://www.tosc.nl",

        # Categories can be used to filter modules in modules listing
        # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
        # for the full list
        'category': 'Others',
        'version': '0.1',

        # any module necessary for this one to work correctly
        'depends': ['data_time_tracker', 'hr', 'product'],

        # always loaded
        'data': [
            # 'security/ir.model.access.csv',
            'views/product_view.xml',
            'views/hr_employee_view.xml',
        ],
        # only loaded in demonstration mode
        'demo': [
            # 'demo/demo.xml',
        ],
    }
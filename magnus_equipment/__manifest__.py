# -*- coding: utf-8 -*-

{
    'name': 'Magnus - Equipments addon',
    'version': '1.0',
    'author'  : 'TOSC - Willem Hulshof',
    'website' : 'http://www.tosc.nl',
    'category': 'Maintenance',
    'description': """Restricting Menu Visibility""",
    'depends': ['hr_maintenance','data_time_tracker'],
    'summary': 'Equipments, Assets, Internal Hardware, Allocation Tracking',
    'data': [
        'security/security.xml',
        'views/maintenance_view.xml',
        'views/maintenance_equipment_view.xml'
    ],

    'installable': True,
    'application': True,
}

# -*- coding: utf-8 -*-

{
    'name': 'Magnus - Equipments addon',
    'version': '1.0',
    'author'  : 'Magnus - Hayo Bos',
    'website' : 'http://www.magnus.nl',
    'category': 'Maintenance',
    'description': """Adds Magnus specific requirements to the existing Equipment Module.""",
    'depends': ['maintenance', 'data_time_tracker', 'account_asset_maintenance'],
    'summary': 'Equipments, Assets, Internal Hardware, Allocation Tracking',
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/maintenance_view.xml',
        'views/maintenance_equipment_view.xml',
        'data/maintenance_data.xml'
    ],
    'installable': True,
    'application': True,
}

# -*- coding: utf-8 -*-
# Copyright 2013-2017 Therp BV <http://therp.nl>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    "name": "Partner Professional Services Relations",
    "version": "10.0.1.0.1",
    "author": "Therp BV,Camptocamp,Magnus,Odoo Community Association (OCA)",
    "complexity": "normal",
    "category": "Customer Relationship Management",
    "license": "AGPL-3",
    "depends": [
        'partner_multi_relation','magnus_account'
    ],
    "demo": [

    ],
    "data": [
        "data/data.xml",
        "views/res_partner_relation_all.xml",
        "views/project_view.xml",
#        'views/res_partner.xml',
#        'views/res_partner_relation_type.xml',
#        'views/menu.xml',
#        'security/ir.model.access.csv',
    ],
    "auto_install": False,
    "installable": True,
}

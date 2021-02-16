# -*- coding: utf-8 -*-
# Copyright 2017 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Magnus customization to the asset equipment link",
    "summary": "Create equipment when validating an invoice with assets",
    "version": "10.0.1.0.0",
    "website": "http://www.magnus.nl",
    "author": "Hayo Bos",
    "license": "AGPL-3",
    "installable": True,
    "depends": [
        "account_asset_maintenance",
        "magnus_equipment"
    ],
    "data": [
        "views/account_asset_asset_views.xml",
        "views/maintenance_equipment_view.xml"
    ],
}
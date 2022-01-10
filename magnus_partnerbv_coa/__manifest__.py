# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

# Copyright (C) 2018 Magnus Red B.V. (<http://www.magnus.nl>).

{
    'name': 'Netherlands - Magnus Partner B.V. Chart of Accounts',
    'version': '3.0',
    'category': 'Localization',
    'author': 'Magnus',
    'website': 'http://www.magnus.nl',
    'depends': [
        'account',
        'base_vat',
        'base_iban',
    ],
    'data': [
        'data/account_account_tag.xml',
        'data/account_chart_template.xml',
        'data/account.account.template.xml',
        'data/account_tax_template.xml',
        'data/account_fiscal_position_template.xml',
        'data/account_fiscal_position_tax_template.xml',
        'data/account_fiscal_position_account_template.xml',
        'data/account_chart_template.yml',
        'data/menuitem.xml',
    ],
    'demo': [],
    'auto_install': False,
    'installable': True,
}

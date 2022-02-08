# Copyright 2021 Hunki Enterprises BV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "v12 invoicing features",
    "summary": "Backport some v12 features",
    "version": "12.0.1.0.0",
    'category': 'Accounting',
    "author": "Hunki Enterprises BV",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": [
        "account",
    ],
    "data": [
        "views/account_invoice.xml",
        "views/account_journal.xml",
    ],
}

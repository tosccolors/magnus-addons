# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "Account Customizations (Magnus)",
    "version": "14.0.1.0.0",
    "license": "AGPL-3",
    "summary": "Adapt account and related modules for magnus",
    "author": "The Open Source Company",
    "website": "http://www.tosc.nl",
    "category": "Accounting & Finance",
    "depends": [
        "account",
        "account_move_cutoff",
        "account_statement_import_online",
    ],
    "installable": True,
    "data": [
        "views/res_config_settings.xml",
    ],
}

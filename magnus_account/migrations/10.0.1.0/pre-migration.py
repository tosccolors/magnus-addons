# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openupgradelib import openupgrade

@openupgrade.migrate(use_env=True)
def migrate(env, version):
    cr = env.cr

    if openupgrade.is_module_installed(env.cr, 'magnus_invoice_layout'):
        openupgrade.update_module_names(
            env.cr,
            [('magnus_invoice_layout', 'magnus_account')],
            merge_modules=True)

    if openupgrade.is_module_installed(env.cr, 'megis_account_invoice_force_number'):
        openupgrade.update_module_names(
            env.cr,
            [('megis_account_invoice_force_number', 'magnus_account')],
            merge_modules=True)

    if openupgrade.is_module_installed(env.cr, 'megis_account_slam'):
        openupgrade.update_module_names(
            env.cr,
            [('megis_account_slam', 'magnus_account')],
            merge_modules=True)

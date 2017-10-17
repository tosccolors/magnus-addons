# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openupgradelib import openupgrade

_xmlid_renames = [
    ('megis_auth.goedk_facturen', 'account_invoice_2step_validation.goedk_facturen'),
    ('megis_auth.authorize', 'account_invoice_2step_validation.authorize'),
    ('megis_auth.verification', 'account_invoice_2step_validation.verification'),
]


def install_new_modules(cr):
    sql = """
    UPDATE ir_module_module
    SET state='to install'
    WHERE name = '%s' AND state='uninstalled'
    """ %('publishing_accounts')
    openupgrade.logged_query(cr, sql)

@openupgrade.migrate(use_env=True)
def migrate(env, version):
    cr = env.cr
    install_new_modules(env.cr)

    openupgrade.rename_xmlids(env.cr, _xmlid_renames)

    if openupgrade.is_module_installed(env.cr, 'nsm_improv02'):
        openupgrade.update_module_names(
            env.cr,
            [('nsm_improv02', 'account_invoice_2step_validation')],
            merge_modules=True)

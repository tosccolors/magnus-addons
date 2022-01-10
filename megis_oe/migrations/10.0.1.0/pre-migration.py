# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openupgradelib import openupgrade

to_install = [
    'publishing_accounts',
    'account_invoice_2step_validation',
    'magnus_account'
]


def install_new_modules(cr):
    sql = """
    UPDATE ir_module_module
    SET state='to install'
    WHERE name in %s AND state='uninstalled'
    """ % (tuple(to_install),)
    openupgrade.logged_query(cr, sql)


@openupgrade.migrate(use_env=True)
def migrate(env, version):
    cr = env.cr
    install_new_modules(env.cr)

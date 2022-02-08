# Copyright 2018 Eficent Business and IT Consulting Services, S.L.
# Copyright 2019 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    # No need to check existence, as if getting to this, it will exist
    openupgrade.rename_fields(
        env, [
            ('attachment.queue', 'attachment_queue', 'sync_date', 'date_done'),
        ],
    )
    # Many2many field
    openupgrade.rename_tables(
        env.cr, [('attachment_base_synchronize_ir_attachment_metadata',
                  'attachment_queue_attachment_queue')],
    )


    
def rename_attachment_queue(cr):
    openupgrade.rename_tables(
        cr, [('ir_attachment_metadata', 'attachment_queue')]
    )
    openupgrade.rename_models(
        cr, [('ir.attachment.metadata', 'attachment.queue')]
    )


# @openupgrade.migrate()
# def migrate(env, version):
#     rename_attachment_queue(env.cr)

# @openupgrade.migrate()
# def migrate(env, version):
#     # No need to check existence, as if getting to this, it will exist

#     # Many2many field
#     openupgrade.rename_tables(
#         env.cr, [('analytic_account_analytic_line',
#                   'magnus_timesheet_timesheet_analytic_line')],
#     )


# def rename_attachment_queue(cr):
#     openupgrade.rename_tables(
#         cr, [('account_analytic_line', 'timesheet_analytic_line')]
#     )
#     openupgrade.rename_models(
#         cr, [('account.analytic.line', 'timesheet.analytic.line')]
#     )


# @openupgrade.migrate()
# def migrate(env, version):
#     rename_attachment_queue(env.cr) 

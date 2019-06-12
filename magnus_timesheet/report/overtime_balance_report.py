# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _

class OvertimeBalanceReport(models.Model):
    _name = 'overtime.balance.report'
    _auto = False
    _description = 'Overtime Balance Report'

    date = fields.Date(
        'Date',
        readonly=True
    )
    user_id = fields.Many2one(
        'res.users',
        string='User',
        readonly=True
    )
    overtime_balanced = fields.Float(
        string="Overtime Balance",
        readonly=True
    )
    overtime_taken = fields.Float(
        string="Overtime Taken",
        readonly=True
    )
    overtime_hrs = fields.Float(
        string="Overtime Hrs",
        readonly=True
    )

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self.env.cr, 'overtime_balance_report')

        self.env.cr.execute("""
                        CREATE OR REPLACE VIEW overtime_balance_report AS (
                        SELECT
                            min(aal.id) AS id,
                            aal.date AS date,
                            aal.user_id AS user_id,
                            SUM(CASE
                                WHEN pp.overtime = 'true'
                                THEN aal.unit_amount
                                ELSE 0
                                END) AS overtime_taken,
                            SUM(CASE
                                WHEN pp.overtime_hrs = 'true'
                                THEN aal.unit_amount
                                ELSE 0
                                END) AS overtime_hrs,                        
                            (
                              SUM(CASE
                                WHEN pp.overtime_hrs = 'true'
                                THEN aal.unit_amount
                                ELSE 0
                                END) -
                              SUM(CASE
                                WHEN pp.overtime = 'true'
                                THEN aal.unit_amount
                                ELSE 0
                                END)
                            ) AS overtime_balanced
                        FROM account_analytic_line aal
                        JOIN account_analytic_account aa ON aa.id = aal.account_id
                        JOIN project_project pp ON pp.analytic_account_id = aa.id
                        WHERE pp.overtime = true OR pp.overtime_hrs = true
                        GROUP BY aal.date, aal.user_id
                        )""")




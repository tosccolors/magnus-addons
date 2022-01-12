# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError

class CrmPipelineActualsReport(models.Model):
    _name = 'crm.pipeline.actuals.report'
    _auto = False
    _description = 'Pipeline Actuals Report'

    lead_id = fields.Many2one(
        'crm.lead',
        string='Opportunity',
        readonly=True
    )
    department_id = fields.Many2one(
        'hr.department',
        string='Practice',
        readonly=True
    )
    partner_id = fields.Many2one(
        'res.partner',
        string='Customer',
        readonly=True
    )
    project_id = fields.Many2one(
        'project.project',
        string='Project',
        readonly=True
    )
    user_id = fields.Many2one(
        'res.users',
        string='Salesperson',
        readonly=True
    )
    name = fields.Char(
        string="Opportunity Name",
        readonly=True
    )
    operating_unit_id = fields.Many2one(
        'operating.unit',
        string='Operating Unit',
        readonly=True
    )
    month = fields.Many2one(
        'date.range',
        string='Month',
        readonly=True
    )
    total_revenue = fields.Float(
        'Total Revenue',
        readonly=True
    )
    total_revenue_per = fields.Float(
        'Total Revenue %',
        readonly=True
    )
    magnus_blue_bv_amount = fields.Float(
        string='Forecast Blue',
        readonly=True
    )
    magnus_blue_bv_per = fields.Float(
        string='Forecast Blue %',
        readonly=True
    )
    magnus_red_bv_amount = fields.Float(
        string='Forecast Red',
        readonly=True
    )
    magnus_red_bv_per = fields.Float(
        string='Forecast Red %',
        readonly=True
    )
    magnus_green_bv_amount = fields.Float(
        string='Forecast Green',
        readonly=True
    )
    magnus_green_bv_per = fields.Float(
        string='Forecast Green %',
        readonly=True
    )
    magnus_black_bv_amount = fields.Float(
        string='Forecast Black',
        readonly=True
    )
    magnus_black_bv_per = fields.Float(
        string='Forecast Black %',
        readonly=True
    )
    total_actuals_amount = fields.Float(
        string='Actuals Total',
        readonly=True
    )
    actuals_red_amount = fields.Float(
        string='Actuals Red',
        readonly=True
    )
    actuals_blue_amount = fields.Float(
        string='Actuals Blue',
        readonly=True
    )
    actuals_green_amount = fields.Float(
        string='Actuals Green',
        readonly=True
    )
    actuals_black_amount = fields.Float(
        string='Actuals Black',
        readonly=True
    )
    actuals_blue_perc = fields.Float(
        string='Actuals Red %',
        readonly=True
    )
    actuals_red_perc = fields.Float(
        string='Actuals Blue %',
        readonly=True
    )
    actuals_green_perc = fields.Float(
        string='Actuals Green %',
        readonly=True
    )
    actuals_black_perc = fields.Float(
        string='Actuals Black %',
        readonly=True
    )

    @api.model_cr
    def init(self):
        """ """
        tools.drop_view_if_exists(self.env.cr, 'crm_pipeline_actuals_report')
        self.env.cr.execute('''
        CREATE OR REPLACE VIEW crm_pipeline_actuals_report AS (
            WITH query01 as (
            SELECT 
                    sum(aal.amount) as amount, 
                    dr.id as month, 
                    aml.operating_unit_id as operating_unit, 
                    pp.id as project_id
            FROM account_analytic_line aal
            LEFT JOIN date_range dr on (
                dr.type_id = 2 AND 
                dr.date_start <= aal.date AND 
                dr.date_end >= aal.date
                )
            LEFT JOIN account_account aa on (
                aal.general_account_id = aa.id
                )
            LEFT JOIN account_move_line aml on (
                aal.move_id = aml.id
                )
            LEFT JOIN project_project pp ON (
                pp.analytic_account_id = aal.account_id
                )
            WHERE 
                aa.code = '8100' AND 
                aal.move_id is not NULL
            GROUP BY 
                dr.id, 
                aml.operating_unit_id,   
                pp.id)
                
                SELECT 
                    crs.id AS id,
                    sum(query01.amount) AS total_actuals_amount,
                    sum(CASE
                        WHEN query01.operating_unit = '6'
                        THEN query01.amount
                        ELSE 0
                    END) AS actuals_red_amount,
                    sum(CASE
                        WHEN query01.operating_unit = '7'
                        THEN query01.amount
                        ELSE 0
                    END) AS actuals_green_amount,
                    sum(CASE
                        WHEN query01.operating_unit = '8'
                        THEN query01.amount
                        ELSE 0
                    END) AS actuals_blue_amount,
                    sum(CASE
                        WHEN query01.operating_unit = '11'
                        THEN query01.amount
                        ELSE 0
                    END) AS actuals_black_amount,
                    crs.project_id AS project_id,
                    crs.month AS month,
                    crs.operating_unit_id AS operating_unit_id,
                    crs.partner_id AS partner_id,
                    crs.user_id AS user_id,
                    crs.department_id AS department_id,
                    crs.name AS name,
                    crs.lead_id AS lead_id,
                    crs.total_revenue AS total_revenue,
                    crs.total_revenue_per AS total_revenue_per,
                    crs.magnus_red_bv_amount AS magnus_red_bv_amount,
                    crs.magnus_blue_bv_amount AS magnus_blue_bv_amount,
                    crs.magnus_green_bv_amount AS magnus_green_bv_amount,
                    crs.magnus_black_bv_amount AS magnus_black_bv_amount,
                    crs.magnus_red_bv_per AS magnus_red_bv_per,
                    crs.magnus_blue_bv_per AS magnus_blue_bv_per,
                    crs.magnus_green_bv_per AS magnus_green_bv_per,
                    crs.magnus_black_bv_per AS magnus_black_bv_per
                FROM 
                    query01
                RIGHT JOIN	crm_revenue_split crs ON (
                    query01.month = crs.month AND
                    query01.project_id = crs.project_id)
                GROUP BY 
                    query01.operating_unit,
                    crs.id,
                    crs.project_id,
                    crs.month,
                    crs.operating_unit_id,
                    crs.partner_id,
                    crs.user_id,
                    crs.department_id,
                    crs.name,
                    crs.lead_id,
                    crs.total_revenue,
                    crs.total_revenue_per,
                    crs.magnus_red_bv_amount,
                    crs.magnus_blue_bv_amount,
                    crs.magnus_green_bv_amount,
                    crs.magnus_black_bv_amount,
                    crs.magnus_red_bv_per,
                    crs.magnus_blue_bv_per,
                    crs.magnus_green_bv_per,
                    crs.magnus_black_bv_per)''')


    @api.model
    def read_group(
            self,
            domain,
            fields,
            groupby,
            offset=0,
            limit=None,
            orderby=False,
            lazy=True
        ):
        res = super(CrmPipelineActualsReport, self).read_group(
            domain,
            fields,
            groupby,
            offset,
            limit=limit,
            orderby=orderby,
            lazy=lazy
        )
        # for index, val in enumerate(res):
        #     res[index]['chargeability'] = \
        #         (res[index]['chargeable_hours'] /
        #         res[index]['norm_hours']) * 100 \
        #             if res[index]['norm_hours'] > 0 else 0.0

        return res

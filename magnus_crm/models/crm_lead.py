# -*- coding: utf-8 -*-
# Copyright 2018 Magnus ((www.magnus.nl).)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _
from datetime import datetime, timedelta
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta

class Lead(models.Model):
    _inherit = "crm.lead"

    start_date = fields.Date('Start Date')
    end_date = fields.Date('End Date')
    project_id = fields.Many2one('project.project', string='Project')
    subject = fields.Char('Subject')
    operating_unit_id = fields.Many2one('operating.unit', string='Operating Unit')
    contract_signed = fields.Boolean(string='Contract Signed')
    department_id = fields.Many2one('hr.department', string='Sales Team')
    expected_duration = fields.Integer(string='Expected Duration')
    monthly_revenue_ids = fields.One2many('crm.monthly.revenue', 'lead_id', string='Monthly Revenue')
    show_button = fields.Boolean(string='Show button')

    @api.onchange('monthly_revenue_ids')
    def onchange_monthly_revenue_ids(self):
        if round(sum(self.monthly_revenue_ids.mapped('nominal_revenue')), 2) != round(self.planned_revenue, 2):
            self.show_button = True
        else:
            self.show_button = False

    @api.one
    def update_monthly_revenue(self):
        self.monthly_revenue_ids = False
        sd = self.start_date
        ed = self.end_date
        if sd and ed:
            sd = datetime.strptime(sd, "%Y-%m-%d").date()
            ed = datetime.strptime(ed, "%Y-%m-%d").date()
            if sd>=ed:
                raise ValidationError(_("End date should be greater than start date."))
            month_end_date = (sd + relativedelta(months=1)).replace(day=1) - timedelta(days=1)
            relativedelta
            if month_end_date > ed:
                month_end_date = ed
            monthly_revenues = []
            total_days = (ed-sd).days + 1
            while True:
                days_per_month = (month_end_date-sd).days + 1
                nominal_revenue_per_month = self.planned_revenue*days_per_month/total_days
                expected_revenue_per_month = (((float(days_per_month)/float(total_days))*self.planned_revenue)*(self.probability/100))
                duration = str(days_per_month)+" days ("+str(sd.day)+"-"+str(month_end_date.day)+" "+str(sd.strftime('%B'))+")"
                monthly_revenues.append((0, 0, {'date': month_end_date, 'month': month_end_date.strftime('%B'),'no_of_days': duration,'expected_revenue': expected_revenue_per_month, 'nominal_revenue': nominal_revenue_per_month,'percentage': self.probability}))
                sd = month_end_date + timedelta(days=1)
                month_end_date = (sd + relativedelta(months=1)).replace(day=1) - timedelta(days=1)
                if sd > ed:
                    break
                if month_end_date > ed:
                    month_end_date = ed
            self.monthly_revenue_ids = monthly_revenues

    @api.one
    def recalculate_total(self):
        if round(sum(self.monthly_revenue_ids.mapped('nominal_revenue')), 2) != round(self.planned_revenue, 2):
            self.planned_revenue = round(sum(self.monthly_revenue_ids.mapped('nominal_revenue')), 2)
            self.show_button = False

    @api.onchange('start_date', 'end_date', 'planned_revenue', 'probability')
    def onchange_date(self):
        self.update_monthly_revenue()

    @api.onchange('partner_id')
    def onchange_partner(self):
        values = {}
        if not self.partner_id:
            return values

        part = self.partner_id
        if part.sector_id:
            values.update({
                'sector_id': part.sector_id,
                'secondary_sector_ids': [(6, 0, part.secondary_sector_ids.ids)],
            })
        else:
            values.update({
                'sector_id': False,
                'secondary_sector_ids': False,
            })
        return {'value' : values}

class MonthlyRevenue(models.Model):
    _name = "crm.monthly.revenue"
    _rec_name = "month"

    month = fields.Char('Month', required=True)
    date = fields.Date('Date')
    no_of_days = fields.Char('Duration', required=True)
    expected_revenue = fields.Float('Expected Revenue', required=True)
    nominal_revenue = fields.Float('Nominal Revenue', required=True)
    percentage = fields.Float(related="lead_id.probability", string='Probability')
    lead_id = fields.Many2one('crm.lead', string='Lead', ondelete='cascade', required=True)
    company_currency = fields.Many2one(string='Currency', related='lead_id.company_id.currency_id', readonly=True, relation="res.currency", store=True)
    user_id = fields.Many2one(related="lead_id.user_id", relation='res.users', string='Salesperson', index=True, store=True)
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
    monthly_revenue_ids = fields.One2many('crm.monthly.revenue', 'lead_id', string='Monthly Revenue')

    @api.onchange('start_date', 'end_date', 'planned_revenue')
    def onchange_date(self):
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
                revenue_per_month = self.planned_revenue*days_per_month/total_days
                duration = str(days_per_month)+" days ("+str(sd.day)+"-"+str(month_end_date.day)+" "+str(sd.strftime('%B'))+")"
                monthly_revenues.append((0, 0, {'month': month_end_date.strftime('%B'),'no_of_days': duration,'expected_revenue': revenue_per_month,'percentage': self.probability}))
                sd = month_end_date + timedelta(days=1)
                month_end_date = (sd + relativedelta(months=1)).replace(day=1) - timedelta(days=1)
                if sd > ed:
                    break
                if month_end_date > ed:
                    month_end_date = ed
            self.monthly_revenue_ids = monthly_revenues

class MonthlyRevenue(models.Model):
    _name = "crm.monthly.revenue"
    _rec_name = "month"

    month = fields.Char('Month', required=True)
    no_of_days = fields.Char('Duration', required=True)
    expected_revenue = fields.Float('Expected Revenue', required=True)
    percentage = fields.Float(related="lead_id.probability", string='Probability')
    lead_id = fields.Many2one('crm.lead', string='Lead', ondelete='cascade', required=True)
    company_currency = fields.Many2one(string='Currency', related='lead_id.company_id.currency_id', readonly=True, relation="res.currency", store=True)
    user_id = fields.Many2one(related="lead_id.user_id", relation='res.users', string='Salesperson', index=True, store=True)
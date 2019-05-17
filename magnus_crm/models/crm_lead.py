# -*- coding: utf-8 -*-
# Copyright 2018 Magnus ((www.magnus.nl).)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _
from datetime import datetime, timedelta
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta

class Lead(models.Model):
    _inherit = "crm.lead"

    @api.one
    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        start_date = self.start_date
        end_date = self.end_date
        if (start_date and end_date) and (start_date > end_date):
            raise ValidationError(_("End date should be greater than start date."))

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
    latest_revenue_date = fields.Date('Latest Revenue Date')
    partner_contact_id = fields.Many2one('res.partner', string='Contact Person')

    

    @api.model
    def default_get(self, fields):
        res = super(Lead, self).default_get(fields)
        context = self._context
        current_uid = context.get('uid')
        user = self.env['res.users'].browse(current_uid)
        res.update({'operating_unit_id':user.default_operating_unit_id.id})
        return res
    
    @api.model
    def create(self, vals):
        res = super(Lead, self).create(vals)
        monthly_revenue_ids = res.monthly_revenue_ids.filtered('date')
        if monthly_revenue_ids:
            res.write({'latest_revenue_date': monthly_revenue_ids.sorted('date')[-1].date})
        return res

    @api.onchange('monthly_revenue_ids')
    def onchange_monthly_revenue_ids(self):
        if round(sum(self.monthly_revenue_ids.mapped('expected_revenue')), 2) != round(self.planned_revenue, 2):
            self.show_button = True
        else:
            self.show_button = False

    @api.one
    def update_monthly_revenue(self):
        manual_lines = []
        sd = self.start_date
        ed = self.end_date
        if sd and ed:
            sd = datetime.strptime(sd, "%Y-%m-%d").date()
            ed = datetime.strptime(ed, "%Y-%m-%d").date()
            if sd > ed:
                raise ValidationError(_("End date should be greater than start date."))

            for line in self.monthly_revenue_ids.filtered(lambda l: not l.computed_line):
                manual_lines.append((4, line.id))

            month_end_date = (sd + relativedelta(months=1)).replace(day=1) - timedelta(days=1)
            relativedelta
            if month_end_date > ed:
                month_end_date = ed
            monthly_revenues = []
            total_days = (ed-sd).days + 1
            while True:
                days_per_month = (month_end_date-sd).days + 1
                expected_revenue_per_month = self.planned_revenue*days_per_month/total_days
                weighted_revenue_per_month = (((float(days_per_month)/float(total_days))*self.planned_revenue)*(self.probability/100))
                days = " days (" if days_per_month > 1 else " day ("
                duration = str(days_per_month) + days + str(sd.day)+"-"+str(month_end_date.day)+" "+str(sd.strftime('%B'))+")"
                monthly_revenues.append((0, 0, {'date': month_end_date, 'latest_revenue_date': month_end_date.replace(day=1) - timedelta(days=1), 'year': month_end_date.year, 'month': month_end_date.strftime('%B'),'no_of_days': duration,'weighted_revenue': weighted_revenue_per_month, 'expected_revenue': expected_revenue_per_month,'percentage': self.probability, 'computed_line': True, 'percentage': self.probability}))
                sd = month_end_date + timedelta(days=1)
                month_end_date = (sd + relativedelta(months=1)).replace(day=1) - timedelta(days=1)
                if sd > ed:
                    break
                if month_end_date > ed:
                    month_end_date = ed
            self.monthly_revenue_ids = monthly_revenues + manual_lines

    @api.one
    def recalculate_total(self):
        if round(sum(self.monthly_revenue_ids.mapped('expected_revenue')), 2) != round(self.planned_revenue, 2):
            self.planned_revenue = round(sum(self.monthly_revenue_ids.mapped('expected_revenue')), 2)
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
        addr = self.partner_id.address_get(['delivery', 'invoice', 'contact'])

        if part.type == 'contact':
            contact = self.env['res.partner'].search([('is_company','=', False),('type','=', 'contact'),('parent_id','=', part.id)])
            if len(contact) >=1:
                contact_id = contact[0]
            else:
                contact_id = False
        elif addr['contact'] == addr['default']:
            contact_id = False
        else: contact_id = addr['contact']

        values.update({'partner_contact_id': contact_id, 'partner_name': part.name})

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

    @api.onchange('partner_contact_id')
    def onchange_contact(self):
        if self.partner_contact_id:
            partner = self.partner_contact_id
            values = {
                'contact_name': partner.name,
                'title': partner.title.id,
                'email_from' : partner.email,
                'phone' : partner.phone,
                'mobile' : partner.mobile,
                'function': partner.function,
            }
        else:
            values = {
                'contact_name': False,
                'title': False,
                'email_from': False,
                'phone': False,
                'mobile': False,
                'function': False,
            }
        return {'value' : values}

class MonthlyRevenue(models.Model):
    _name = "crm.monthly.revenue"
    _rec_name = "month"

    @api.model
    def default_get(self, fields):
        res = super(MonthlyRevenue, self).default_get(fields)
        ctx = self.env.context.copy()
        if 'default_lead_id' in ctx:
            crm_obj = self.env['crm.lead'].browse(ctx['default_lead_id'])
            latest_revenue_date = crm_obj.latest_revenue_date or crm_obj.start_date or datetime.now().strftime("%Y-%m-%d")
            if latest_revenue_date:
                latest_revenue_date = datetime.strptime(latest_revenue_date, "%Y-%m-%d").date()
                upcoming_month_end_date = (latest_revenue_date + relativedelta(months=2)).replace(day=1) - timedelta(days=1)
                res['date'] = upcoming_month_end_date.strftime("%Y-%m-%d")
                res['latest_revenue_date'] = latest_revenue_date.strftime("%Y-%m-%d")
        return res

    date = fields.Date('Date', required=True)
    year = fields.Char(string='Year')
    month = fields.Char(string='Month')
    no_of_days = fields.Char(string='Duration')
    latest_revenue_date = fields.Date('Latest Revenue Date')
    weighted_revenue = fields.Float('Weighted Revenue', required=True)
    expected_revenue = fields.Float('Expected Revenue', required=True)
    percentage = fields.Float(string='Probability')
    lead_id = fields.Many2one('crm.lead', string='Opportunity', ondelete='cascade', required=True)
    company_currency = fields.Many2one(string='Currency', related='lead_id.company_id.currency_id', readonly=True, relation="res.currency", store=True)
    user_id = fields.Many2one(related="lead_id.user_id", relation='res.users', string='Salesperson', index=True, store=True)
    computed_line = fields.Boolean(string="Computed line")
    project_id = fields.Many2one('project.project', related='lead_id.project_id', string='Project', store=True)
    partner_id = fields.Many2one('res.partner', related='lead_id.partner_id', string='Customer', store=True)
    sector_id = fields.Many2one('res.partner.sector', related='lead_id.sector_id', string='Main Sector', store=True)
    department_id = fields.Many2one('hr.department', related='lead_id.department_id', string='Sales Team', store=True)

    @api.onchange('expected_revenue', 'percentage')
    def onchagne_expected_revenue(self):
        if self.expected_revenue:
            self.weighted_revenue = self.expected_revenue*self.percentage/100
        else:
            self.weighted_revenue = 0

    @api.onchange('date')
    def onchange_date(self):
        ctx = self.env.context.copy()
        lead_id = ctx.get('default_lead_id')
        date = datetime.strptime(self.date, "%Y-%m-%d").date()

        if date and self.latest_revenue_date:
            lrd = datetime.strptime(self.latest_revenue_date, "%Y-%m-%d").date()
            if date < lrd or (date.month == lrd.month and date.year == lrd.year):
                date = self.date = (lrd + relativedelta(months=2)).replace(day=1) - timedelta(days=1)

        if date:
            days = " days (" if date.day > 1 else " day ("
            self.no_of_days = str(date.day)+days+str(1)+"-"+str(date.day)+" "+str(date.strftime('%B'))+")"
            self.month = date.strftime('%B')
            self.year = date.year

        if lead_id and date:
            lead = self.env['crm.lead'].browse([lead_id])
            self.env.cr.execute("""
                            UPDATE %s SET latest_revenue_date = '%s'
                            WHERE id = %s
                  """ % (lead._table, date, lead_id))
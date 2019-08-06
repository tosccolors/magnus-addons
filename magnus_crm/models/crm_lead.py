# -*- coding: utf-8 -*-
# Copyright 2018 Magnus ((www.magnus.nl).)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _
from datetime import datetime, timedelta
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta
import json


class Lead(models.Model):
    _inherit = "crm.lead"

    @api.one
    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        start_date = self.start_date
        end_date = self.end_date
        if (start_date and end_date) and (start_date > end_date):
            raise ValidationError(_("End date should be greater than start date."))

    @api.depends('operating_unit_id')
    @api.one
    def _compute_dept_ou_domain(self):
        """
        Compute the domain for the department domain.
        """
        department_ids = []
        if self.operating_unit_id:
            self.env.cr.execute("""
                            SELECT id
                            FROM hr_department
                            WHERE operating_unit_id = %s 
                            AND parent_id IS NULL
                            """
                            % (self.operating_unit_id.id))

            result = self.env.cr.fetchall()
            for res in result:
                department_id = res[0]
                self.env.cr.execute("""
                    WITH RECURSIVE
                        subordinates AS(
                            SELECT id, parent_id  FROM hr_department WHERE id = %s
                            UNION
                            SELECT h.id, h.parent_id FROM hr_department h
                            INNER JOIN subordinates s ON s.id = h.parent_id)
                        SELECT  *  FROM subordinates"""
                            % (department_id))
                result2 = self.env.cr.fetchall()
                for res2 in result2:
                    department_ids.append(res2[0])
        self.dept_ou_domain = json.dumps(
            [('id', 'in', department_ids)]
        )


    start_date = fields.Date('Start Date')
    end_date = fields.Date('End Date')
    project_id = fields.Many2one('project.project', string='Project')
    subject = fields.Char('Subject')
    operating_unit_id = fields.Many2one('operating.unit', string='Operating Unit', required=True)
    contract_signed = fields.Boolean(string='Contract Signed')
    department_id = fields.Many2one('hr.department', string='Practice')
    expected_duration = fields.Integer(string='Expected Duration')
    monthly_revenue_ids = fields.One2many('crm.monthly.revenue', 'lead_id', string='Monthly Revenue')
    show_button = fields.Boolean(string='Show button')
    latest_revenue_date = fields.Date('Latest Revenue Date')
    partner_contact_id = fields.Many2one('res.partner', string='Contact Person')
    revenue_split_ids = fields.One2many('crm.revenue.split', 'lead_id', string='Revenue')
    dept_ou_domain = fields.Char(compute=_compute_dept_ou_domain, readonly=True, store=False, )


    @api.model
    def _onchange_stage_id_values(self, stage_id):
        """ returns the new values when stage_id has changed """
        crm_stage = self.env['crm.stage']
        res = super(Lead,self)._onchange_stage_id_values(stage_id)
        for rec in self.monthly_revenue_ids:
            rec.update({'percentage':res.get('probability')})
        print ("self.stage_id.show_when_chaing",self.stage_id.show_when_chaing)
        print ("self.stage_id.requirements",self.stage_id.requirements)
        if self.stage_id.show_when_chaing:
            if self.stage_id.requirements:
                text = self.stage_id.requirements
                self.env.user.notify_info(message=text,sticky=True)
        return res

    
    @api.depends('operating_unit_id')
    @api.onchange('operating_unit_id')
    def onchange_operating_unit_id(self):
        for rec in self.revenue_split_ids:
            blue_per = 0.0
            red_per = 0.0
            green_per =0.0
            black_per = 0.0
            magnus_blue_bv_amount = 0.0
            magnus_red_bv_amount = 0.0
            magnus_green_bv_amount = 0.0
            magnus_black_bv_amount = 0.0
            rec.magnus_blue_bv_per = 0.0
            rec.magnus_blue_bv_amount = 0.0
            rec.magnus_red_bv_amount = 0.0
            rec.magnus_red_bv_per = 0.0
            rec.magnus_green_bv_per = 0.0
            rec.magnus_green_bv_amount = 0.0
            rec.magnus_black_bv_per = 0.0
            rec.magnus_black_bv_amount = 0.0
            if self.operating_unit_id.name == 'Magnus Blue B.V.':
                rec.magnus_blue_bv_per = 100
                rec.magnus_blue_bv_amount = rec.total_revenue
            if self.operating_unit_id.name == 'Magnus Red B.V.':
                rec.magnus_red_bv_amount = rec.total_revenue
                rec.magnus_red_bv_per = 100
            if self.operating_unit_id.name == 'Magnus Green B.V.':
                rec.magnus_green_bv_per = 100
                rec.magnus_green_bv_amount = rec.total_revenue
            if self.operating_unit_id.name == 'Magnus Black B.V.':
                rec.magnus_black_bv_per = 100
                rec.magnus_black_bv_amount = rec.total_revenue
            
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
#             if sd > ed:
#                 raise ValidationError(_("End date should be greater than start date."))

            for line in self.monthly_revenue_ids.filtered(lambda l: not l.computed_line):
                manual_lines.append((4, line.id))

            month_end_date = (sd + relativedelta(months=1)).replace(day=1) - timedelta(days=1)
            relativedelta
            if month_end_date > ed:
                month_end_date = ed
            monthly_revenues = []
            monthly_revenues_split = []
            total_days = (ed-sd).days + 1
            date_range = self.env['date.range']
            company = self.company_id.id or self.env.user.company_id.id

            while True:
                common_domain = [('date_start', '<=', month_end_date), ('date_end', '>=', month_end_date), ('company_id', '=', company)]
                month = date_range.search(common_domain+[('type_id.fiscal_month', '=', True)])
                year = date_range.search(common_domain + [('type_id.fiscal_year', '=', True)])
                days_per_month = (month_end_date-sd).days + 1
                expected_revenue_per_month = self.planned_revenue*days_per_month/total_days
                weighted_revenue_per_month = (((float(days_per_month)/float(total_days))*self.planned_revenue)*(self.probability/100))
                days = " days (" if days_per_month > 1 else " day ("
                duration = str(days_per_month) + days + str(sd.day)+"-"+str(month_end_date.day)+" "+str(sd.strftime('%B'))+")"
                monthly_revenues.append((0, 0,
                                         {'date': month_end_date, 'latest_revenue_date': month_end_date.replace(day=1) - timedelta(days=1),
                                          'year': year.id, 'month': month.id,
                                          'no_of_days': duration,'weighted_revenue': weighted_revenue_per_month,
                                          'expected_revenue': expected_revenue_per_month,'percentage': self.probability,
                                          'computed_line': True, 'percentage': self.probability}))

                blue_per = 0.0
                red_per = 0.0
                green_per =0.0
                black_per = 0.0
                magnus_blue_bv_amount = 0.0
                magnus_red_bv_amount = 0.0
                magnus_green_bv_amount = 0.0
                magnus_black_bv_amount = 0.0
                if self.operating_unit_id.name == 'Magnus Blue B.V.':
                    blue_per = 100
                    magnus_blue_bv_amount = expected_revenue_per_month
                if self.operating_unit_id.name == 'Magnus Red B.V.':
                    red_per = 100
                    magnus_red_bv_amount = expected_revenue_per_month
                if self.operating_unit_id.name == 'Magnus Green B.V.':
                    green_per = 100
                    magnus_green_bv_amount = expected_revenue_per_month
                if self.operating_unit_id.name == 'Magnus Black B.V.':
                    black_per = 100
                    magnus_black_bv_amount = expected_revenue_per_month

                monthly_revenues_split.append((0,0,{
                                                    'month': month.id,
                                                    'total_revenue': expected_revenue_per_month,
                                                    'total_revenue_per':100,
                                                    'magnus_blue_bv_per':blue_per,
                                                    'magnus_red_bv_per':red_per,
                                                    'magnus_black_bv_per':black_per,
                                                    'magnus_green_bv_per':green_per,
                                                    'magnus_blue_bv_amount':magnus_blue_bv_amount,
                                                    'magnus_red_bv_amount':magnus_red_bv_amount,
                                                    'magnus_green_bv_amount':magnus_green_bv_amount,
                                                    'magnus_black_bv_amount':magnus_black_bv_amount,
                                                    
                                                    }))
                sd = month_end_date + timedelta(days=1)
                month_end_date = (sd + relativedelta(months=1)).replace(day=1) - timedelta(days=1)
                if sd > ed:
                    break
                if month_end_date > ed:
                    month_end_date = ed
            self.monthly_revenue_ids = monthly_revenues + manual_lines
            self.revenue_split_ids = monthly_revenues_split

    @api.one
    def recalculate_total(self):
        if round(sum(self.monthly_revenue_ids.mapped('expected_revenue')), 2) != round(self.planned_revenue, 2):
            self.planned_revenue = round(sum(self.monthly_revenue_ids.mapped('expected_revenue')), 2)
            self.show_button = False

    @api.onchange('start_date', 'end_date', 'planned_revenue', 'probability')
    def onchange_date(self):
        if self.start_date and not self._origin.end_date and self.start_date > self.end_date:
            self.end_date = self.start_date
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
    year = fields.Many2one('date.range', string='Year')
    month = fields.Many2one('date.range', string='Month')
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
    department_id = fields.Many2one('hr.department', related='lead_id.department_id', string='Practice', store=True)
    operating_unit_id = fields.Many2one('operating.unit', related='lead_id.operating_unit_id', string='Operating Unit', store=True)

    def calculate_weighted_revenue(self, percentage):
        self.ensure_one()
        weighted_revenue = 0
        if self.expected_revenue:
            weighted_revenue = self.expected_revenue * percentage / 100
        return weighted_revenue

    @api.onchange('expected_revenue', 'percentage', 'lead_id.probability')
    def onchagne_expected_revenue(self):
        self.percentage = self.lead_id.probability
        self.weighted_revenue = self.calculate_weighted_revenue(self.percentage)

    @api.onchange('date')
    def onchange_date(self):
        ctx = self.env.context.copy()
        lead_id = ctx.get('default_lead_id')
        date = datetime.strptime(self.date, "%Y-%m-%d").date()
        date_range = self.env['date.range']

        if date and self.latest_revenue_date:
            lrd = datetime.strptime(self.latest_revenue_date, "%Y-%m-%d").date()
            if date < lrd or (date.month == lrd.month and date.year == lrd.year):
                date = self.date = (lrd + relativedelta(months=2)).replace(day=1) - timedelta(days=1)

        if date:
            days = " days (" if date.day > 1 else " day ("
            self.no_of_days = str(date.day)+days+str(1)+"-"+str(date.day)+" "+str(date.strftime('%B'))+")"
            company = self.lead_id.company_id.id or self.env.user.company_id.id
            common_domian = [('date_start', '<=', self.date), ('date_end', '>=', self.date), ('company_id', '=', company)]
            month = date_range.search(common_domian+[('type_id.fiscal_month', '=', True)])
            self.month = month.id
            year = date_range.search(common_domian+[('type_id.fiscal_year', '=', True)])
            self.year = year.id

        if lead_id and date:
            lead = self.env['crm.lead'].browse([lead_id])
            self.env.cr.execute("""
                            UPDATE %s SET latest_revenue_date = '%s'
                            WHERE id = %s
                  """ % (lead._table, date, lead_id))

class CRMRevenueSplit(models.Model):
    _name = "crm.revenue.split"
    
    lead_id = fields.Many2one('crm.lead', string='Opportunity', ondelete='cascade')
    
    department_id = fields.Many2one('hr.department', related='lead_id.department_id', string='Practice', store=True)
    partner_id = fields.Many2one('res.partner', related='lead_id.partner_id', string='Customer', store=True)
    project_id = fields.Many2one('project.project', related='lead_id.project_id', string='Project', store=True)
    user_id = fields.Many2one('res.users', related='lead_id.user_id', string='Salesperson', store=True)
    name = fields.Char(related='lead_id.name',string="Opportunity Name",store=True)
    operating_unit_id = fields.Many2one('operating.unit', related='lead_id.operating_unit_id', string='Operating Unit', store=True)
    month = fields.Many2one('date.range', string='Month')
    total_revenue = fields.Float('Total Revenue')
    total_revenue_per = fields.Float('Total Revenue %')
    magnus_blue_bv_amount = fields.Float(oldname='mangnus_blue_bv_amount', string='Magnus Blue B.V.')
    magnus_blue_bv_per = fields.Float(oldname='mangnus_blue_bv_per', string='Magnus Blue B.V. %')
    magnus_red_bv_amount = fields.Float(oldname='mangnus_red_bv_amount', string='Magnus Red B.V.')
    magnus_red_bv_per = fields.Float(oldname='mangnus_red_bv_per', string='Magnus Red B.V. %')
    magnus_green_bv_amount = fields.Float(oldname='mangnus_green_bv_amount', string='Magnus Green B.V.')
    magnus_green_bv_per = fields.Float(oldname='mangnus_green_bv_per', string='Magnus Green B.V. %')
    magnus_black_bv_amount = fields.Float(oldname='mangnus_black_bv_amount', string='Magnus Black B.V.')
    magnus_black_bv_per = fields.Float(oldname='mangnus_black_bv_per', string='Magnus Black B.V. %')
    
    @api.one
    @api.constrains('magnus_blue_bv_per', 'magnus_red_bv_per','magnus_green_bv_per','magnus_black_bv_per')
    def _check_dates(self):
        total_per = self.magnus_blue_bv_per + self.magnus_red_bv_per + self.magnus_green_bv_per + self.magnus_black_bv_per
        if int(total_per) > 100:
            raise ValidationError(_("Total Percentage should be equal to 100"))
        
    @api.onchange('magnus_black_bv_per')
    def onchange_magnus_black_perc(self):
        """ Magnus Green B.V. """
        total_per = self.magnus_blue_bv_per + self.magnus_red_bv_per + self.magnus_green_bv_per + self.magnus_black_bv_per
        if  int(total_per) > 100:
            self.magnus_black_bv_per = 0.0
            raise ValidationError(
                    _("Total Percentage should be equal to 100"))
        # if self.magnus_black_bv_per > 0.0:
        self.magnus_black_bv_amount = self.total_revenue * (self.magnus_black_bv_per / 100)
              
    @api.onchange('magnus_black_bv_amount')
    def onchange_magnus_black_amount(self):
        """ Magnus Green B.V. """
        self.magnus_black_bv_per = self.magnus_black_bv_amount * (100/self.total_revenue)
        
    @api.onchange('magnus_blue_bv_per')
    def onchange_magnus_blue_per(self):
        """ for Magnus Blue B.V """
        total_per = self.magnus_blue_bv_per + self.magnus_red_bv_per + self.magnus_green_bv_per + self.magnus_black_bv_per
        if  int(total_per) > 100:
            self.magnus_blue_bv_per = 0.0
            raise ValidationError(
                    _("Total Percentage should be equal to 100"))
        # if self.magnus_blue_bv_per > 0:
        self.magnus_blue_bv_amount = self.total_revenue * (self.magnus_blue_bv_per / 100)
            
    @api.onchange('magnus_blue_bv_amount')
    def onchange_magnus_blue_amount(self):
        """ for Magnus Blue B.V """
        if self.magnus_blue_bv_amount > 0.0:
            self.magnus_blue_bv_per = self.magnus_blue_bv_amount * (100/self.total_revenue)
        
            
    @api.onchange('magnus_red_bv_per')
    def onchange_magnus_red_per(self):
        total_per = self.magnus_blue_bv_per + self.magnus_red_bv_per + self.magnus_green_bv_per + self.magnus_black_bv_per
        if  int(total_per) > 100:
            self.magnus_red_bv_per = 0.0
            raise ValidationError(
                    _("Total Percentage should be equal to 100"))
        self.magnus_red_bv_amount = self.total_revenue * (self.magnus_red_bv_per / 100)
            
    @api.onchange('magnus_red_bv_amount')
    def onchange_magnus_red_amount(self):
        """ for Magnus Red B.V """
        if self.magnus_red_bv_amount > 0:
            self.magnus_red_bv_per = self.magnus_red_bv_amount * (100/self.total_revenue)
            
    @api.onchange('magnus_green_bv_per')
    def onchange_magnus_green_per(self):
        """ Magnus Green B.V. """
        total_per = self.magnus_blue_bv_per + self.magnus_red_bv_per + self.magnus_green_bv_per + self.magnus_black_bv_per
        if  int(total_per) > 100:
            self.magnus_green_bv_per = 0.0
            raise ValidationError(_("Total Percentage should be equal to 100"))
            
        # if self.magnus_green_bv_per > 0.0:
        self.magnus_green_bv_amount = self.total_revenue * (self.magnus_green_bv_per / 100)
            
    @api.onchange('magnus_green_bv_amount')
    def onchange_magnus_green_amount(self):
        """ Magnus Green B.V. """
        if self.magnus_green_bv_amount > 0:
            self.magnus_green_bv_per = self.magnus_green_bv_amount * (100/self.total_revenue)
            
    
class CRMStage(models.Model):
    _inherit = "crm.stage"
    
    show_when_chaing = fields.Boolean("Show when changing")
            
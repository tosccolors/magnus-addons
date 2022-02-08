# -*- coding: utf-8 -*-
from odoo import api, fields, models

    

class CreditControlStatus(models.TransientModel):
    _name = "open.invoice.status"
    
    company_id = fields.Many2one('res.company', string='Company')
    operating_unit_id = fields.Many2one('operating.unit', string='Operating unit')
    
    invoice_id = fields.Many2one('account.invoice', string='Invoice id')
    partner_id = fields.Many2one('res.partner', string='Partner')
    phone = fields.Char(related='partner_id.phone', string='Phone')
    account_manager = fields.Many2one('res.users', string='Account manager')
    
    currency_id = fields.Many2one('res.currency', string='Currency')
    amount_total_company_signed = fields.Monetary(string='Total due', currency_field='currency_id')
    date_invoice = fields.Date(string='Invoice date')
    date_due = fields.Date(string='Date due')
    payment_mode = fields.Many2one('account.payment.mode',string='Payment mode')
    date_latest_cc = fields.Date(string='Latest credit control')

    credit_control_line_ids = fields.Many2many('credit.control.line', string="Credit control lines")
    latest_credit_control_line_id = fields.Many2one('credit.control.line', string='Latest credit control line')
    cc_state = fields.Selection(related='latest_credit_control_line_id.state', string='State')
    cc_channel = fields.Selection(related='latest_credit_control_line_id.channel', string='Channel')
    cc_level = fields.Integer(related='latest_credit_control_line_id.level', string='Level')
    cc_policy_level = fields.Char(string='Policy level')
    
    invoice_state = fields.Char(string='Invoice state')
    processed = fields.Boolean(string='Done') 

    @api.multi
    def accept(self) :
    	for line in self:
	        line.processed = True
	        for lines in line.latest_credit_control_line_id:
	        	lines.state='sent'   #i.e. Done
        return

    #show records selected by sql query
    @api.multi
    def default_view(self):
        #clear table, then fill with current status
        self.env['open.invoice.status'].search([]).unlink()
        open_invoices = self.env['account.invoice'].search([('state','=','open'),('type','like','%out%')])
        for invoice in open_invoices :
            last_cc_action =self.env['credit.control.line'].search([('invoice_id','=',invoice.id)], order='date desc', limit=1)
            cc_actions = self.env['credit.control.line'].search([('invoice_id','=',invoice.id)])
            if last_cc_action.state in ['sent', 'done'] :
            	processed = True
            else :
            	processed = False
            vals = {'company_id'           : invoice.company_id.id,
                    'operating_unit_id'    : invoice.operating_unit_id.id,
                    'invoice_id'           : invoice.id,
                    'partner_id'           : invoice.partner_id.id,
                    'account_manager'      : invoice.partner_id.user_id.id or invoice.partner_id.parent_id.user_id.id,
                    'processed'            : processed,
                    'currency_id'          : invoice.currency_id.id,
                    'amount_total_company_signed' :invoice.amount_total_company_signed,
                    'date_invoice'         : invoice.date_invoice,
                    'date_due'             : invoice.date_due,
                    'payment_mode'         : invoice.payment_mode_id.id,
                    'date_latest_cc'       : last_cc_action.date,
                    'invoice_state'        : invoice.state,
                    'cc_policy_level'      : last_cc_action.policy_level_id.name,
                    'latest_credit_control_line_id' : last_cc_action.id,
                    'credit_control_line_ids' : [(6,0,cc_actions.ids)]
                   }
            #sign correction
            if invoice.type=='out_invoice' and invoice.amount_total_company_signed < 0 :
            	vals['amount_total_company_signed'] = -vals['amount_total_company_signed']
            self.create(vals)
        #prepare for showing. (note: show all records because when using res_id no search filter appears and no button is possible)
        res_ids = self.search([]).ids
        action = {
                    "type"     : "ir.actions.act_window",
                    "res_model": "open.invoice.status",
                    "name"     : "Open invoice status",
                    "views": [[False, "tree"], [False, "form"]]
        }
        return action 




 


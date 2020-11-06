# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime,timedelta

class FleetWizard(models.TransientModel):
    _name = "fleet.wizard"
    _description = "Fleet Wizard"

    license_plate = fields.Many2one('fleet.vehicle','License Plate')
    driver_id = fields.Many2one('res.partner', 'Driver')
    date = fields.Datetime('Date')
    odometer_value = fields.Float('Odometer Value')
    add = fields.Boolean()

    @api.onchange('add')
    def onchange_add(self):
        domain = {}
        if self.add:
            license_plate_no_driver = self.env['fleet.vehicle'].search([('driver_id', '=', False)]).mapped('id')
            domain['license_plate'] = [('id', 'in', license_plate_no_driver)]
        else:
            license_plate_driver = self.env['fleet.vehicle'].search([('driver_id', '!=', False)]).mapped('id')
            domain['license_plate'] = [('id', 'in', license_plate_driver)]
        return {'domain': domain}

    @api.onchange('license_plate')
    def onchange_license_plate(self):
        # import pdb;
        # pdb.set_trace();
        value, domain = {}, {}
        fleet_obj = self.env['fleet.vehicle']
        if not self.add:
           fleet = fleet_obj.search([('id', '=', self.license_plate.id)])
           if len(fleet) == 1:
                value['driver_id'] = fleet.driver_id.id
        employees = self.env['hr.employee'].search([]).mapped('user_id.partner_id.id')
        domain['driver_id'] = [('id', 'in', employees)]
        return {'value':value, 'domain':domain}

    @api.multi
    def add_driver(self):
        fleet_obj = self.env['fleet.vehicle']
        data_tracker = self.env['data.time.tracker']
        fleet = fleet_obj.search([('id', '=', self.license_plate.id)])
        driver_fleet = fleet_obj.search([('driver_id', '=', self.driver_id.id)])
        if not fleet:
            raise UserError(_("Can't find vehicle with license_plate %s")%(self.license_plate))
        elif driver_fleet:
            raise UserError(_("The driver already owns a vehicle %s")%(driver_fleet.license_plate))
        elif fleet:
            sdomain = [('model', '=', fleet._name), ('relation_model', '=', self.driver_id._name),
                       ('model_ref', '=', fleet.id),('type_many2many', '=', False)]

            trackObj = data_tracker.search(sdomain, limit=1)
            fleet.write({'driver_id': self.driver_id.id, 'odometer':self.odometer_value})
            if trackObj.date_from < self.date:
                trackObj.write({'date_to': self.date})
        #updating Date from to next sunday
        data_tracker_update=data_tracker.search([('id', '=', fleet.model_track_ids[-1].id)])
        data_tracker_update.sudo().write({'date_from': self.date_from_next_sunday()})
        return True

    @api.multi
    def remove_driver(self):
        fleet_obj = self.env['fleet.vehicle']
        data_tracker = self.env['data.time.tracker']

        fleet = fleet_obj.search([('id', '=', self.license_plate.id), ('driver_id', '=', self.driver_id.id)])

        # sdomain = [('model', '=', fleet._name), ('relation_model', '=', self.driver_id._name),
        #            ('model_ref', '=', fleet.id),('type_many2many', '=', False)]
        #
        # trackObj = data_tracker.search(sdomain, limit=1)

        data = {'driver_id':False}

        if 'terminate' in self.env.context:
            data['active'] = False
            fleet.log_contracts.contract_close()
        fleet.write(data)
        # if trackObj.date_from < self.date:
        #     trackObj.write({'date_to':self.date})
        data_tracker_update = data_tracker.search([('id', '=', fleet.model_track_ids[-1].id)])
        data_tracker_update.sudo().write({'date_to': self.date_from_next_sunday()})
        return True

    #To update the given date into next sunday of week
    api.multi
    def date_from_next_sunday(self):
        covert_date = self.date.split(' ')
        year = int(covert_date[0].split('-')[0])
        month = int(covert_date[0].split('-')[1])
        day = int(covert_date[0].split('-')[2])
        getday = datetime(year, month, day).weekday()
        nextsunday = str(datetime(year, month, day) + timedelta(days=6 - getday))
        return nextsunday
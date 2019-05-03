# -*- coding: utf-8 -*-
from odoo import http

# class FleetTimeTracker(http.Controller):
#     @http.route('/fleet_time_tracker/fleet_time_tracker/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/fleet_time_tracker/fleet_time_tracker/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('fleet_time_tracker.listing', {
#             'root': '/fleet_time_tracker/fleet_time_tracker',
#             'objects': http.request.env['fleet_time_tracker.fleet_time_tracker'].search([]),
#         })

#     @http.route('/fleet_time_tracker/fleet_time_tracker/objects/<model("fleet_time_tracker.fleet_time_tracker"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('fleet_time_tracker.object', {
#             'object': obj
#         })
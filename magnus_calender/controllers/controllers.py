# -*- coding: utf-8 -*-
from odoo import http

# class MagnusCalender(http.Controller):
#     @http.route('/magnus_calender/magnus_calender/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/magnus_calender/magnus_calender/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('magnus_calender.listing', {
#             'root': '/magnus_calender/magnus_calender',
#             'objects': http.request.env['magnus_calender.magnus_calender'].search([]),
#         })

#     @http.route('/magnus_calender/magnus_calender/objects/<model("magnus_calender.magnus_calender"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('magnus_calender.object', {
#             'object': obj
#         })
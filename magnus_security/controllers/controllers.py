# -*- coding: utf-8 -*-
from odoo import http

# class MagnusSecurity(http.Controller):
#     @http.route('/magnus_security/magnus_security/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/magnus_security/magnus_security/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('magnus_security.listing', {
#             'root': '/magnus_security/magnus_security',
#             'objects': http.request.env['magnus_security.magnus_security'].search([]),
#         })

#     @http.route('/magnus_security/magnus_security/objects/<model("magnus_security.magnus_security"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('magnus_security.object', {
#             'object': obj
#         })
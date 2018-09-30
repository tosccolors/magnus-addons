# -*- coding: utf-8 -*-
from odoo import http

# class MagnusInvoicing(http.Controller):
#     @http.route('/magnus_invoicing/magnus_invoicing/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/magnus_invoicing/magnus_invoicing/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('magnus_invoicing.listing', {
#             'root': '/magnus_invoicing/magnus_invoicing',
#             'objects': http.request.env['magnus_invoicing.magnus_invoicing'].search([]),
#         })

#     @http.route('/magnus_invoicing/magnus_invoicing/objects/<model("magnus_invoicing.magnus_invoicing"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('magnus_invoicing.object', {
#             'object': obj
#         })
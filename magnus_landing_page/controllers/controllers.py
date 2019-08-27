# -*- coding: utf-8 -*-
from odoo import http

# class MagnusLandingPage(http.Controller):
#     @http.route('/magnus_landing_page/magnus_landing_page/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/magnus_landing_page/magnus_landing_page/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('magnus_landing_page.listing', {
#             'root': '/magnus_landing_page/magnus_landing_page',
#             'objects': http.request.env['magnus_landing_page.magnus_landing_page'].search([]),
#         })

#     @http.route('/magnus_landing_page/magnus_landing_page/objects/<model("magnus_landing_page.magnus_landing_page"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('magnus_landing_page.object', {
#             'object': obj
#         })
# -*- coding: utf-8 -*-
from odoo import http

# class MagnusExpense(http.Controller):
#     @http.route('/magnus_expense/magnus_expense/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/magnus_expense/magnus_expense/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('magnus_expense.listing', {
#             'root': '/magnus_expense/magnus_expense',
#             'objects': http.request.env['magnus_expense.magnus_expense'].search([]),
#         })

#     @http.route('/magnus_expense/magnus_expense/objects/<model("magnus_expense.magnus_expense"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('magnus_expense.object', {
#             'object': obj
#         })
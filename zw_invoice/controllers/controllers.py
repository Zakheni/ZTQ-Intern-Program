from odoo import http
from odoo.http import request
import json

class CustomerController(http.Controller):
    @http.route('/api/partners/waste', auth='public', methods=['GET'], csrf=False)
    def get_waste_customers(self, **kwargs):
        partners = request.env['res.partner'].sudo().search([('is_waste_customer', '=', True)])
        return request.make_response(json.dumps({
            'customers': [{
                'id': p.id,
                'name': p.name,
                'email': p.email,
                'mine_ids': [mine.id for mine in p.mine_ids]
            } for p in partners]
        }), headers={'Content-Type': 'application/json'})

    @http.route('/api/partners/waste', auth='public', methods=['POST'], csrf=False)
    def create_waste_customer(self, **kwargs):
        data = json.loads(request.httprequest.data)
        partner = request.env['res.partner'].sudo().create({
            'name': data.get('name'),
            'email': data.get('email'),
            'phone': data.get('phone'),
            'is_waste_customer': True,
            'mine_ids': [(6, 0, data.get('mine_ids', []))]
        })
        return request.make_response(json.dumps({'id': partner.id}), headers={'Content-Type': 'application/json'})
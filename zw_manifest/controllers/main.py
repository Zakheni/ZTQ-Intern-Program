from odoo import http
from odoo.http import request
from odoo.exceptions import ValidationError

class ManifestController(http.Controller):
    @http.route('/zw_manifest/update', type='json', auth='user', methods=['POST'])
    def update_manifest(self, manifest_id, status, signature_driver=None):
        try:

            if not request.env.user.has_group('zw_user.group_driver'):
                return {'status': 'error', 'message': 'Unauthorized access'}
            

            manifest = request.env['waste.manifest'].sudo().browse(int(manifest_id))
            if not manifest.exists():
                return {'status': 'error', 'message': 'Manifest not found'}
            

            if manifest.waste_type_id.name == 'Hazardous Waste' and not manifest.dt_number:
                return {'status': 'error', 'message': 'DT Number required for hazardous waste'}
            

            valid_statuses = ['booked', 'generated', 'scheduled', 'delivered', 'authorized']
            if status not in valid_statuses:
                return {'status': 'error', 'message': 'Invalid status'}
            manifest.write({'status': status, 'signature_driver': signature_driver})
            

            manifest.action_advance_status()
            return {'status': 'success', 'message': 'Manifest updated', 'manifest_id': manifest.manifest_id}
        
        except Exception as e:
            return {'status': 'error', 'message': str(e)}


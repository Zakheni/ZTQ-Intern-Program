import datetime
from email.policy import default
from Tools.scripts.texi2html import kwprog
from odoo import models, fields, api
from odoo.exceptions import ValidationError

class ProductProduct(models.Model):
    _inherit = 'product.product'
    is_asset =fields.Boolean(string="Is Asset",default=False)


class StockQuant(models.Model):
    _inherit = 'stock.quant'

    bin_number = fields.Char(string='Bin Number')
    waste_type = fields.Char(string='Waste Type')
    waste_description = fields.Text(string='Waste Description')
    mine_id = fields.Many2one('mine.mine', string='Mine')
    condition = fields.Selection([('intact', 'Intact'), ('broken', 'Broken')], string='Condition')
    bin_type = fields.Char(string='Bin Type')
    location = fields.Char(string='Bin Location')
    audit_ids = fields.One2many('bin.audit', 'bin_id', string='Audits')

class BinAudit(models.Model):
    _name = 'bin.audit'
    _description = 'Bin Audit'

    auditor_id = fields.Char(string = "Auditor ID",required =True)
    bin_id = fields.Many2one('stock.quant', string='Bin', required=True)
    audit_date = fields.Datetime(string = "Audit Date", required=True,default= datetime.date)
    month_year = fields.Char(string='Month/Year', required=True)
    mine_id = fields.Many2one('mine.mine', string='Mine')
    status = fields.Selection([('created', 'Created'), ('finished', 'Finished')], string='Status', default='created')
    condition = fields.Selection([('intact','Intact'),('damaged','Damaged')],string="Condition",
                                 required=True)


class FleetVehicle(models.Model):
    _inherit = 'fleet.vehicle'

    mass = fields.Float(string='Vehicle Mass')
    inspection_ids = fields.One2many('fleet.vehicle.inspection', 'vehicle_id', string='Inspections')
    log_ids = fields.One2many('fleet.vehicle.log', 'vehicle_id', string='Vehicle Logs')

class FleetVehicleInspection(models.Model):
    _name = 'fleet.vehicle.inspection'
    _description = 'Vehicle Inspection'

    vehicle_id = fields.Many2one('fleet.vehicle', string='Vehicle', required=True)
    fault_status = fields.Selection([('clear', 'Clear'), ('fault', 'Fault')], string='Fault Status')
    comment = fields.Text(string='Comment')
    image = fields.Binary(string='Image of Verification')

class FleetVehicleLog(models.Model):
    _name = 'fleet.vehicle.log'
    _description = 'Vehicle Log'

    vehicle_id = fields.Many2one('fleet.vehicle', string='Vehicle', required=True)
    driver_id = fields.Many2one('res.users', string='Driver')
    load_count = fields.Integer(string='Loads')
    date = fields.Date(string='Date', default=fields.Date.today)

    @api.constrains('vehicle_id')
    def _check_vehicle_status(self):
        for record in self:
            if record.vehicle_id.inspection_ids and any(inspection.fault_status == 'fault' for inspection in record.vehicle_id.inspection_ids):
                raise ValidationError("Cannot assign faulty vehicle!")

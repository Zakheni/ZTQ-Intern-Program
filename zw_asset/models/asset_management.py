# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
import logging

_logger = logging.getLogger(__name__)

class ProductProduct(models.Model):
    _inherit = 'product.product'

    is_asset = fields.Boolean(string="Is Asset", default=False)
    bin_size = fields.Selection([
        ('6m3', '6 m³'),
        ('11m3', '11 m³'),
        ('18m3', '18 m³')
    ], string='Bin Size', required=True)

class BinAudit(models.Model):
    _name = 'bin.audit'
    _description = 'Bin Audit History'

    name = fields.Char(string='Reference', required=True,
                      default=lambda self: self.env['ir.sequence'].next_by_code('bin.audit'))
    bin_id = fields.Many2one('stock.quant', string='Bin', required=True, ondelete='cascade')
    auditor_id = fields.Many2one('res.users', string="Auditor", required=True)
    audit_date = fields.Datetime(string="Audit Date", default=fields.Datetime.now)
    month_year = fields.Char(string='Month/Year', required=True)
    mine_id = fields.Many2one('mine.mine', string='Mine')
    status = fields.Selection([
        ('created', 'Created'),
        ('finished', 'Finished')
    ], string='Status', default='created')
    condition = fields.Selection([
        ('intact', 'Intact'),
        ('damaged', 'Damaged')
    ], string="Condition", required=True)

class BinInspection(models.Model):
    _name = 'bin.inspection'
    _description = 'Bin Inspection'

    name = fields.Char(string='Reference', required=True,
                      default=lambda self: self.env['ir.sequence'].next_by_code('bin.inspection'))
    bin_id = fields.Many2one('stock.quant', string='Bin', required=True, ondelete='cascade')
    inspection_date = fields.Datetime(string="Inspection Date", default=fields.Datetime.now)
    fault_status = fields.Selection([
        ('clear', 'Clear'),
        ('fault', 'Fault')
    ], string='Fault Status')
    comment = fields.Text(string='Comment')
    image = fields.Binary(string='Image')

class StockQuant(models.Model):
    _inherit = 'stock.quant'

    bin_number = fields.Char(string='Bin Number', required=True, copy=False)
    waste_type = fields.Char(string='Waste Type')
    waste_description = fields.Text(string='Waste Description')
    mine_id = fields.Many2one('mine.mine', string='Mine')
    collection_area_id = fields.Many2one(
        'waste.collection.area',
        string='Collection Area',
        domain="[('mine_id', '=', mine_id)]"
    )
    condition = fields.Selection([
        ('good', 'Good'),
        ('fair', 'Fair'),
        ('poor', 'Poor'),
        ('damaged', 'Damaged')
    ], string='Condition', required=True)
    bin_type = fields.Char(string='Bin Type')
    bin_size = fields.Selection([
        ('6m3', '6 m³'),
        ('11m3', '11 m³'),
        ('18m3', '18 m³')
    ], string='Bin Size',
        default='6m3',
        required=True)
    location_id = fields.Many2one(
        'stock.location',
        string='Location',
        domain="[('id', 'in', available_location_ids)]",
        required=True
    )
    available_location_ids = fields.Many2many(
        'stock.location',
        compute='_compute_available_locations',
        string='Available Locations'
    )
    audit_ids = fields.One2many(
        'bin.audit',
        'bin_id',
        string='Audit History'
    )
    inspection_ids = fields.One2many(
        'bin.inspection',
        'bin_id',
        string='Inspections'
    )
    assign_to_mine = fields.Boolean(string="Assign to Mine")
    collected_bin = fields.Selection([
        ('draft', 'Draft'),
        ('open', 'In Use'),
        ('done', 'Collected')
    ], string='Collection Status', default='draft')
    display_location = fields.Char(
        string='Location Display',
        compute='_compute_display_location',
        store=True
    )

    _sql_constraints = [
        ('bin_number_unique', 'UNIQUE(bin_number)', 'Bin Number must be unique!')
    ]

    @api.onchange('assign_to_mine', 'mine_id')
    def _onchange_assign_to_mine(self):
        for record in self:
            if not record.assign_to_mine:
                record.update({
                    'mine_id': False,
                    'collection_area_id': False,
                    'waste_type': False,
                    'waste_description': False,
                    'location_id': self.env.ref('stock.stock_location_stock').id
                })
            elif record.mine_id:
                record.location_id = record.mine_id.location_id

    @api.onchange('location_id', 'product_id')
    def _onchange_location_or_product_id(self):

        for record in self:
            if record.location_id and record.product_id:
                quant = self.env['stock.quant'].search([
                    ('location_id', '=', record.location_id.id),
                    ('product_id', '=', record.product_id.id),
                    ('lot_id', '=', record.lot_id.id if record.lot_id else False)
                ], limit=1)
                record.quantity = quant.quantity if quant else 0.0

    @api.model
    def default_get(self, fields):
        res = super(StockQuant, self).default_get(fields)

        bin_product = self.env.ref('zw_asset.product_product_bin', raise_if_not_found=False)
        if not bin_product:
            bin_product = self.env['product.product'].search([('is_asset', '=', True)], limit=1)
            if not bin_product:
                bin_product = self.env['product.product'].create({
                    'name': 'Standard Bin',
                    'is_asset': True,
                    'type': 'product',
                    'bin_size': '6m3',
                    'categ_id': self.env.ref('product.product_category_all').id
                })

        defaults = {
            'product_id': bin_product.id,
            'bin_number': self.env['ir.sequence'].next_by_code('stock.quant.bin.number'),
            'location_id': self.env.ref('stock.stock_location_stock').id,
            'condition': 'good',
            'collected_bin': 'draft',
            'assign_to_mine': False,
            'bin_size': '6m3'
        }

        for field, value in defaults.items():
            if field in fields and not res.get(field):
                res[field] = value

        return res

    @api.model
    def create(self, vals):
        if not vals.get('product_id'):
            bin_product = self.env.ref('zw_asset.product_product_bin', raise_if_not_found=False)
            if not bin_product:
                bin_product = self.env['product.product'].search([('is_asset', '=', True)], limit=1)
                if not bin_product:
                    raise UserError(_("No bin product configured. Please create a product with 'Is Asset' checked."))
            vals['product_id'] = bin_product.id

        if not vals.get('location_id'):
            vals['location_id'] = self.env.ref('stock.stock_location_stock').id

        if not vals.get('bin_number'):
            vals['bin_number'] = self.env['ir.sequence'].next_by_code('stock.quant.bin.number')

        return super(StockQuant, self).create(vals)

    @api.depends('location_id', 'mine_id', 'assign_to_mine')
    def _compute_display_location(self):
        for record in self:
            if record.assign_to_mine and record.mine_id:
                # Display format: "Mine Name (Location Name)"
                record.display_location = f"{record.mine_id.name} ({record.location_id.display_name})"
            else:
                record.display_location = record.location_id.display_name if record.location_id else "Undefined"





    @api.onchange('collected_bin')
    def _onchange_collected_bin(self):
        for record in self:
            if record.collected_bin == 'done':
                record.location_id = self.env.ref('stock.stock_location_stock').id

    @api.depends('mine_id')
    def _compute_available_locations(self):
        for record in self:
            locations = self.env['stock.location']
            if record.mine_id:
                locations |= record.mine_id.location_id
                locations |= self.env['waste.collection.area'].search([
                    ('mine_id', '=', record.mine_id.id)
                ]).mapped('location_id')
            locations |= self.env['stock.warehouse'].search([]).mapped('lot_stock_id')
            record.available_location_ids = locations

    def action_assign_to_mine(self):

        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'stock.domain.wizard',
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'default_bin_id': self.id,
                'default_assign_to_mine': True,
            }
        }

    def action_delete_damaged(self):

        damaged_bins = self.filtered(lambda r: r.condition == 'damaged')
        if not damaged_bins:
            raise ValidationError(_("Only bins with 'Damaged' condition can be deleted!"))
        return damaged_bins.unlink()

    @api.onchange('mine_id')
    def _onchange_mine_id(self):

        for record in self:
            if record.mine_id and record.mine_id.location_id:
                record.location_id = record.mine_id.location_id




class FleetVehicleInspection(models.Model):
    _name = 'fleet.vehicle.inspection'
    _description = 'Vehicle Inspection'

    vehicle_id = fields.Many2one('fleet.vehicle', string='Vehicle', required=True)
    fault_status = fields.Selection([('clear', 'Clear'), ('fault', 'Fault')], string='Fault Status')
    comment = fields.Text(string='Comment')
    image = fields.Binary(string='Image')

class FleetVehicleLog(models.Model):
    _name = 'fleet.vehicle.log'
    _description = 'Vehicle Log'

    vehicle_id = fields.Many2one('fleet.vehicle', string='Vehicle', required=True)
    driver_id = fields.Many2one('res.users', string='Driver')
    assistant_driver_id = fields.Many2one('res.users', string='Assistant Driver')
    load_count = fields.Integer(string='Loads')
    date = fields.Date(string='Date', default=fields.Date.today)

    @api.constrains('vehicle_id')
    def _check_vehicle_status(self):
        for record in self:
            if record.vehicle_id.inspection_ids.filtered(lambda i: i.fault_status == 'fault'):
                raise ValidationError(_("Cannot assign faulty vehicle!"))

class FleetVehicle(models.Model):
    _inherit = 'fleet.vehicle'

    mass = fields.Float(string='Vehicle Mass')
    is_trailer = fields.Boolean(string='Is Trailer', default=False)
    trailer_size = fields.Selection([
        ('10m3', '10 m³'),
        ('20m3', '20 m³')
    ], string='Trailer Size')
    inspection_ids = fields.One2many(
        'fleet.vehicle.inspection',
        'vehicle_id',
        string='Inspections'
    )
    log_ids = fields.One2many(
        'fleet.vehicle.log',
        'vehicle_id',
        string='Vehicle Logs'
    )
    assistant_driver_id = fields.Many2one('res.users', string='Assistant Driver')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('approved', 'Approved')
    ], string='Status', default='draft')

class StockDomainWizard(models.TransientModel):
    _name = 'stock.domain.wizard'
    _description = 'Assign Bin to Mine Wizard'

    bin_id = fields.Many2one('stock.quant', string='Bin', required=True)
    assign_to_mine = fields.Boolean(string="Assign to Mine", default=True)
    mine_id = fields.Many2one('mine.mine', string='Mine', required=True)
    location_id = fields.Many2one('stock.location', string='Location')

    @api.onchange('mine_id')
    def _onchange_mine_id(self):

        for record in self:
            if record.mine_id and record.mine_id.location_id:
                record.location_id = record.mine_id.location_id.id


    def action_confirm(self):
        self.ensure_one()
        if not self.mine_id.location_id:
            raise UserError(_("Selected mine has no location configured!"))

        self.bin_id.write({
            'assign_to_mine': True,
            'mine_id': self.mine_id.id,
            'location_id': self.mine_id.location_id.id,
        })

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'stock.quant',
            'view_mode': 'tree',
            'target': 'current',
            'domain': [('id', '=', self.bin_id.id)]
        }

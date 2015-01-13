#  -*- coding: utf-8 -*-
# 
# 
#     OpenERP, Open Source Management Solution
#     Copyright (C) 2011 NovaPoint Group LLC (<http://www.novapointgroup.com>)
#     Copyright (C) 2004-2010 OpenERP SA (<http://www.openerp.com>)
# 
#     This program is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
# 
#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
# 
#     You should have received a copy of the GNU General Public License
#     along with this program.  If not, see <http://www.gnu.org/licenses/>
##############################################################################

from collections import OrderedDict
from openerp.osv import osv, fields
from mailrun.stock import stock_location as parent_stock_location

_PARENT_LOCATION_WEIGHTS = parent_stock_location._location_weights
_PARENT_LOCATION_WEIGHT_VALUES = sorted(parent_stock_location._location_weights.values())

class stock_picking(osv.osv):
    _inherit = 'stock.picking'
    _columns = {
        'picking_printed': fields.datetime('Picking List Printed', readonly=True),
    }
stock_picking()


class stock_picking_out(osv.osv):
    _inherit = 'stock.picking.out'
    _columns = {
        'picking_printed': fields.datetime('Picking List Printed', readonly=True),
    }
stock_picking_out()

class stock_location(osv.osv):
    _inherit = 'stock.location'
    _columns = {
        'volume_type': fields.selection([('hva', 'HVA'), ('lva', 'LVA')], 'Volume Type'),
        'product_bin_location_info_id': fields.one2many(
            'product.bin.location.info', 'location_id', "Product Bin Location Information"
        )
    }

    _location_weights = OrderedDict(_PARENT_LOCATION_WEIGHTS.items() + [
        ('primary_bin', _PARENT_LOCATION_WEIGHT_VALUES[-1] * 2),
        ('in_stock_2', _PARENT_LOCATION_WEIGHT_VALUES[-1] * 4),
    ])

    def location_weight(self, cr, uid, location, product, preferred_locations=[]):
        weight = super(stock_location, self).location_weight(
            cr, uid, location, product, preferred_locations=preferred_locations)
        location = self.pool.get("stock.location").browse(cr, uid, location.id)

        relevant_bins = [b for b in location.product_bin_location_info_id if b.product_id.id == product.id]
        if relevant_bins and relevant_bins[0].storage_type == "primary":
            weight += self._location_weights['primary_bin']

        if weight & _PARENT_LOCATION_WEIGHTS['in_stock'] == _PARENT_LOCATION_WEIGHTS['in_stock']:
            weight += self._location_weights['in_stock_2']

        return weight

    def highest_weighted_bin_location(self, cr, uid, product, preferred_locations=[]):
        location_pool = self.pool.get("stock.location")
        bin_pool = self.pool.get("product.bin.location.info")

        bin_locations = [b.location_id for b in bin_pool.browse(cr, uid, bin_pool.search(
            cr, uid, [('product_id', '=', product.id)]))]

        sorted_locations = sorted(bin_locations, key=lambda loc: location_pool.location_weight(
            cr, uid, loc, product, preferred_locations=preferred_locations
        ))

        return sorted_locations[-1] if sorted_locations else None

stock_location()

class stock_packages(osv.osv):

    _inherit = 'stock.packages'
    
    def print_label(self, cr, uid, ids, context=None):
        res = super(stock_packages, self).print_label(cr, uid, ids, context=context)
        ir_model_data = self.pool.get('ir.model.data')
        try:
            template_id = ir_model_data.get_object_reference(cr, uid, 'hotp_stock', 'hotp_stock_confirm_email_template')[1]
        except ValueError:
            template_id = False
        self.pool.get('email.template').send_mail(cr, uid, template_id, ids[0], force_send=True, context=context)
        return res

class stock_inventory_line(osv.osv):
    _inherit = "stock.inventory.line"

    _defaults = {
        'location_id': False
    }

    def on_change_product_id(self, cr, uid, ids, location_id, product, uom=False, to_date=False):
        res = super(stock_inventory_line, self).on_change_product_id(cr, uid, ids, location_id, product, uom, to_date)
        res.update({'domain' : {'location_id':[('id', 'in', [])]}})
        res['value'].update({'location_id':False})
        pool_loc = self.pool.get('product.bin.location.info')
        if not product:
            return res

        bin_location_ids = pool_loc.search(cr, uid, [('product_id','=',product)])
        if not bin_location_ids:
            return res
        bin_location_ids = [x.location_id.id for x in pool_loc.browse(cr, uid, bin_location_ids)]
        res['value'].update({'location_id': bin_location_ids[0]})
        res.update({'domain' : {'location_id':[('id', 'in', bin_location_ids)]}})
        return res
    
    def on_change_loc_id(self, cr, uid, ids, location_id, product, uom=False, to_date=False):
        res = {'value': {}}
        if not (product and location_id):
            return res
        pool_loc = self.pool.get('product.bin.location.info')
        bin_location_ids = pool_loc.search(cr, uid, [('product_id','=',product),('location_id','=',location_id)])
        if not bin_location_ids:
            return res
        res['value'].update({'product_qty': pool_loc.browse(cr, uid, bin_location_ids[0]).qty_available})
        return res
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
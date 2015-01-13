import hashlib, itertools
from copy import copy
from collections import OrderedDict
from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp import netsvc, SUPERUSER_ID

class sale_order(osv.Model):
    _inherit = 'sale.order'

    def _prepare_order_line_procurement(self, cr, uid, order, line, move_id, date_planned, context=None):
        location_pool = self.pool.get("stock.location")
        location = line.product_id.primary_bin_location_id

        inventory_pool = self.pool.get('stock.inventory.line')
        location_ids = [int(l.id) for l in set(itertools.chain.from_iterable(
            [l.parent_location_ids + [l] for l in [i.location_id for i in inventory_pool.browse(
                cr, uid, inventory_pool.search(cr, uid, [('product_id', '=', line.product_id.id)])
            )]]
        ))]

        if location.id not in location_ids:
            potential_locations = location_pool.browse(cr, uid, self.pool.get(
                'product.product').get_location_ids(cr, uid, [line.product_id.id], context=context), context=context)
        else:
            potential_locations = location_pool.browse(cr, uid, location_ids)

        if potential_locations:
            location = sorted(
                potential_locations, key=lambda loc: location_pool.location_weight(
                    cr, uid, loc, line.product_id, preferred_locations=[location]
                ), reverse=True
            )[0]

        return {
            'name': line.name,
            'origin': order.name,
            'date_planned': date_planned,
            'product_id': line.product_id.id,
            'product_qty': line.product_uom_qty,
            'product_uom': line.product_uom.id,
            'product_uos_qty': (line.product_uos and line.product_uos_qty)\
                    or line.product_uom_qty,
            'product_uos': (line.product_uos and line.product_uos.id)\
                    or line.product_uom.id,
            'location_id': location.id,
            'procure_method': line.type,
            'move_id': move_id,
            'company_id': order.company_id.id,
            'note': line.name,
        }

    def _prepare_order_line_move(self, cr, uid, order, line, picking_id, date_planned, context=None):
        location_pool = self.pool.get("stock.location")
        location = line.product_id.primary_bin_location_id
        output = order.shop_id.warehouse_id.lot_output_id

        inventory_pool = self.pool.get('stock.inventory.line')
        location_ids = [int(l.id) for l in set(itertools.chain.from_iterable(
            [l.parent_location_ids + [l] for l in [i.location_id for i in inventory_pool.browse(
                cr, uid, inventory_pool.search(cr, uid, [('product_id', '=', line.product_id.id)])
            )]]
        ))]

        if location.id not in location_ids:
            location = order.shop_id.warehouse_id.lot_input_id
            warehouse_pool = self.pool.get("stock.warehouse")
            warehouse = warehouse_pool.browse(cr, SUPERUSER_ID, order.shop_id.warehouse_id.id, context=context)
            potential_locations = []

            for w in warehouse.shared_warehouse_ids:
                intersection = [l for l in w.lot_stock_id.parent_location_ids if l.id in location_ids]
                if w.lot_stock_id.id in location_ids or intersection:
                    potential_locations.append((w.lot_stock_id, w.lot_output_id))
        else:
            potential_locations = [(l, order.shop_id.warehouse_id.lot_output_id)
                                   for l in location_pool.browse(cr, SUPERUSER_ID, location_ids)
            ]

        if potential_locations:
            location, output = sorted(
                potential_locations, key=lambda l: location_pool.location_weight(cr, uid, l[0], line.product_id)
            )[-1]

        return {
            'name': line.name,
            'picking_id': picking_id,
            'product_id': line.product_id.id,
            'date': date_planned,
            'date_expected': date_planned,
            'product_qty': line.product_uom_qty,
            'product_uom': line.product_uom.id,
            'product_uos_qty': (line.product_uos and line.product_uos_qty) or line.product_uom_qty,
            'product_uos': (line.product_uos and line.product_uos.id)\
                    or line.product_uom.id,
            'product_packaging': line.product_packaging.id,
            'partner_id': line.address_allotment_id.id or order.partner_shipping_id.id,
            'location_id': location.id,
            'location_dest_id': output.id,
            'sale_line_id': line.id,
            'tracking_id': False,
            'state': 'draft',
            #'state': 'waiting',
            'company_id': order.company_id.id,
            'price_unit': line.product_id.standard_price or 0.0
        }

sale_order()



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
            location = sorted(potential_locations, key=lambda loc: location_pool.location_weight(
                cr, uid, loc, line.product_id, preferred_locations=[location]
            ))[-1]

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
            potential_stock_location_ids = self.pool.get(
                'product.product').get_location_ids(cr, uid, [line.product_id.id], context=context)
            potential_stock_locations = location_pool.browse(cr, uid, potential_stock_location_ids)

            output_locations = dict([
                (w.lot_stock_id.id, w.lot_output_id) for w in warehouse_pool.browse(
                    cr, uid, warehouse_pool.search(cr, uid, [('lot_stock_id', 'in', potential_stock_location_ids)])
                )])

            potential_locations = []
            for loc in potential_stock_locations:
                potential_location = (loc, order.shop_id.warehouse_id.lot_output_id)

                for parent_id in sorted([p.id for p in loc.parent_location_ids], reverse=True):
                    if parent_id in output_locations:
                        potential_location = (loc, output_locations[parent_id])
                        break

                potential_locations.append(potential_location)
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



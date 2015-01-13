from openerp import netsvc
from openerp.osv import fields, osv, orm

class mrp_production(osv.osv):
    _inherit = 'mrp.production'

    def _make_production_line_procurement(self, cr, uid, production_line, shipment_move_id, context=None):
        wf_service = netsvc.LocalService("workflow")
        procurement_order = self.pool.get('procurement.order')
        production = production_line.production_id

        location_id = self.pool.get("stock.location").highest_weighted_bin_location(
            cr, uid, production_line.product_id, preferred_locations=[production.location_src_id]).id

        date_planned = production.date_planned
        procurement_name = (production.origin or '').split(':')[0] + ':' + production.name
        procurement_id = procurement_order.create(cr, uid, {
                    'name': procurement_name,
                    'origin': procurement_name,
                    'date_planned': date_planned,
                    'product_id': production_line.product_id.id,
                    'product_qty': production_line.product_qty,
                    'product_uom': production_line.product_uom.id,
                    'product_uos_qty': production_line.product_uos and production_line.product_qty or False,
                    'product_uos': production_line.product_uos and production_line.product_uos.id or False,
                    'location_id': location_id,
                    'procure_method': production_line.product_id.procure_method,
                    'move_id': shipment_move_id,
                    'company_id': production.company_id.id,
                })
        wf_service.trg_validate(uid, procurement_order._name, procurement_id, 'button_confirm', cr)
        return procurement_id

    def _make_production_internal_shipment_line(self, cr, uid, production_line, shipment_id, parent_move_id, destination_location_id=False, context=None):
        stock_move = self.pool.get('stock.move')
        production = production_line.production_id
        date_planned = production.date_planned
        # Internal shipment is created for Stockable and Consumer Products
        if production_line.product_id.type not in ('product', 'consu'):
            return False

        source_location_id = self.pool.get("stock.location").highest_weighted_bin_location(
            cr, uid, production_line.product_id, preferred_locations=[production.location_src_id]).id

        if not destination_location_id:
            destination_location_id = source_location_id
        return stock_move.create(cr, uid, {
                        'name': production.name,
                        'picking_id': shipment_id,
                        'product_id': production_line.product_id.id,
                        'product_qty': production_line.product_qty,
                        'product_uom': production_line.product_uom.id,
                        'product_uos_qty': production_line.product_uos and production_line.product_uos_qty or False,
                        'product_uos': production_line.product_uos and production_line.product_uos.id or False,
                        'date': date_planned,
                        'move_dest_id': parent_move_id,
                        'location_id': source_location_id,
                        'location_dest_id': destination_location_id,
                        'state': 'waiting',
                        'company_id': production.company_id.id,
                })

    def _make_production_consume_line(self, cr, uid, production_line, parent_move_id, source_location_id=False, context=None):
        stock_move = self.pool.get('stock.move')
        production = production_line.production_id
        # Internal shipment is created for Stockable and Consumer Products
        if production_line.product_id.type not in ('product', 'consu'):
            return False
        destination_location_id = production.product_id.property_stock_production.id

        if not source_location_id:
            source_location_id = self.pool.get("stock.location").highest_weighted_bin_location(
                cr, uid, production_line.product_id, preferred_locations=[production.location_src_id]).id

        move_id = stock_move.create(cr, uid, {
            'name': production.name,
            'date': production.date_planned,
            'product_id': production_line.product_id.id,
            'product_qty': production_line.product_qty,
            'product_uom': production_line.product_uom.id,
            'product_uos_qty': production_line.product_uos and production_line.product_uos_qty or False,
            'product_uos': production_line.product_uos and production_line.product_uos.id or False,
            'location_id': source_location_id,
            'location_dest_id': destination_location_id,
            'move_dest_id': parent_move_id,
            'state': 'waiting',
            'company_id': production.company_id.id,
        })
        production.write({'move_lines': [(4, move_id)]}, context=context)
        return move_id

    def action_confirm(self, cr, uid, ids, context=None):
        """ Confirms production order.
        @return: Newly generated Shipment Id.
        """
        shipment_id = False
        wf_service = netsvc.LocalService("workflow")
        uncompute_ids = filter(lambda x:x, [not x.product_lines and x.id or False for x in self.browse(cr, uid, ids, context=context)])
        self.action_compute(cr, uid, uncompute_ids, context=context)

        for production in self.browse(cr, uid, ids, context=context):
            shipment_id = self._make_production_internal_shipment(cr, uid, production, context=context)
            produce_move_id = self._make_production_produce_line(cr, uid, production, context=context)

            # Take routing location as a Source Location.
            default_source_location = production.location_src_id

            if production.bom_id.routing_id and production.bom_id.routing_id.location_id:
                default_source_location = production.bom_id.routing_id.location_id

            for line in production.product_lines:
                source_location_id = self.pool.get("stock.location").highest_weighted_bin_location(
                    cr, uid, line.product_id, preferred_locations=[production.location_src_id]).id

                consume_move_id = self._make_production_consume_line(
                    cr, uid, line, produce_move_id, source_location_id=source_location_id, context=context)

                shipment_move_id = self._make_production_internal_shipment_line(
                    cr, uid, line, shipment_id, consume_move_id,
                    destination_location_id=source_location_id, context=context)

                self._make_production_line_procurement(cr, uid, line, shipment_move_id, context=context)

            wf_service.trg_validate(uid, 'stock.picking', shipment_id, 'button_confirm', cr)
            production.write({'state':'confirmed'}, context=context)

        return shipment_id

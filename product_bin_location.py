# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2011 NovaPoint Group LLC (<http://www.novapointgroup.com>)
#    Copyright (C) 2004-2010 OpenERP SA (<http://www.openerp.com>)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>
#
##############################################################################

from openerp.osv import osv, fields

class product_bin_location_info(osv.osv):

    def _calc_stock(self, cr, uid, ids, name, args, context=None):
        res = {}
        if context is None:
            context = {}

        for multi_location in self.pool.get('product.bin.location.info').browse(cr, uid, ids, context=context):
            context['location'] = multi_location.location_id.id
            context['no_warehouse_sharing'] = True
            context['compute_child'] = False
            stock_data = multi_location.product_id._product_available(field_names=['qty_available', 'virtual_available'], context=context)
            if multi_location.product_id.id in stock_data:
                res[multi_location.id] = stock_data[multi_location.product_id.id]
        return res

    def _get_location_bin_id(loc_pool, cr, uid, ids, context=None):
        return loc_pool.pool.get("product.bin.location.info").search(cr, uid, [('location_id', 'in', ids)])

    _name = "product.bin.location.info"
    _rec_name = 'location_id'
    _columns = {
        'company_id': fields.related(
            'location_id', 'company_id', type='many2one', relation='res.company', string='Company', readonly=True,
            store={"product.location": (_get_location_bin_id, ['company_id'], 10),
                   "product.bin.location.info": (lambda pool, cr, uid, ids, context: ids, ['location_id'], 10)}),

        'storage_type': fields.selection([
            ('primary', 'Primary'),
            ('overstock', 'Overstock')
            ], 'Storage Type', help='Storage type of the location.  Options are:  Primary, Overstock ', select=1, required=True),
        'location_id': fields.many2one('stock.location', 'Location', required=True, help='This is the location where the product is located.',
                                         select=1),
        'qty_available': fields.function(_calc_stock, multi="stock", method=True,
                type='float', string='Real Stock', help='This is the real stock for each specific location.'),
        'virtual_available': fields.function(_calc_stock, multi="stock", method=True,
            type='float', string='Virtual Stock', help='This is the virtual  Stock for each  specific location.'),
        'immediately_usable_stock': fields.float('Immediately Usable Stock', help='This is the immediately usable stock by location.'),
        'bom_stock_value': fields.float('BoM Stock Value', help='This is the calculated BoM Stock available by  location '),
        'product_id': fields.many2one('product.product', 'Product', required=True)
    }
    _defaults = {
        'storage_type': 'primary'
    }
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

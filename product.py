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
from openerp import SUPERUSER_ID

class product_product(osv.osv):
    _inherit = 'product.product'

    def _primary_bin_location_id(self, cr, uid, ids, field_name, args, context=None):
        res = {}
        products = self.browse(cr, uid, ids, context=context)
        curr_company = self.pool.get("res.users").browse(cr, uid, uid, context=context).company_id

        for product in products:
            location_id = None

            for bin in product.multi_bin_ids:
                if bin.storage_type != 'primary':
                    continue

                if bin.location_id.calculated_company_id.id == curr_company.id or not location_id:
                    location_id = bin.location_id.id

            res[product.id] = location_id

        return res

    def _multi_bin_ids(self, cr, uid, ids, field, arg, context=None):
        location_ids = super(product_product, self).get_location_ids(cr, uid, ids, context=context)
        bin_pool = self.pool.get('product.bin.location.info')

        return dict([(prod_id, bin_pool.search(
            cr, uid, [('product_id', '=', prod_id), ('location_id', 'child_of', location_ids)],
            context=context)) for prod_id in ids])

    _columns = {
        'primary_bin_location_id': fields.function(
            _primary_bin_location_id, type='many2one', readonly=True, relation="stock.location", string="Bin", method=True
        ),
        'multi_bin_ids': fields.function(_multi_bin_ids, type="one2many", obj='product.bin.location.info',
                                              method=True, string='Product Bins'),
        'default_code':  fields.char('Reference', size=64, required=True)
    }
    
    def _check_storage_type(self, cr, uid, ids, context=None):
        product_ids = self.browse(cr, uid, ids, context=context)
        for product_id in product_ids:
            primary = False
            for multi_loc_id in product_id.multi_bin_ids:
                if multi_loc_id.storage_type == 'primary' and primary:
                    return False
                elif multi_loc_id.storage_type == 'primary':
                    primary = True
        return True

    def get_location_ids(self, cr, uid, ids, context=None):
        if context is None:
            context = {}

        location_ids = super(product_product, self).get_location_ids(cr, uid, ids, context=context) + [
            b.location_id.id for p in self.browse(cr, uid, ids, context=context) for b in p.multi_bin_ids
        ]

        return location_ids

    _constraints = [
        #(_check_storage_type, 'You cannot create more than one multilocation lines with storage type primary.', ['Storage Type'] )
        ]
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
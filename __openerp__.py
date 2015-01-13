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
{
    'name': 'Warehouse Customizations for HOTP',
    'version': '0.06',
    'category': 'Warehouse',
    'description': """
   This module adds customizations to the stock module.
    """,
    'author': 'NovaPoint Group LLC',
    'website': ' http://www.novapointgroup.com',
    'depends': ['stock', 'sale_stock','shipping_api','mailrun'],
    'data': [
           'security/ir.model.access.csv',
           'product_bin_location_view.xml',
           'product_view.xml',
           'stock_inventory_view.xml',
           'stock_view.xml',
           'hotp_stock_email_template.xml',
           'report/picking_sheet_view.xml',
           'filter.yml'
    ],
    'demo': [],
    'test': [
        'test/basic_quantity.xml',
        'test/basic_quantity.yml',
        'test/manufacturing.xml',
        'test/manufacturing.yml',
        'test/sale_order.xml',
        'test/sale_order.yml'
    ],
    'auto_install': False,
    'installable': True,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

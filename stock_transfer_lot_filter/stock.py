# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) Rooms For (Hong Kong) Limited T/A OSCG (<http://www.openerp-asia.net>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp.osv import fields, osv
from openerp.tools.translate import _


class stock_production_lot(osv.osv):
    _inherit = 'stock.production.lot'

    def _compute_balance(self, cr, uid, ids, fieldnames, args, context=None):
        res = dict.fromkeys(ids, 0)
        int_loc_ids = self.pool.get('stock.location').search(cr, uid, [('usage','=','internal')])
        for rec in self.browse(cr, uid, ids):
            quant_obj = self.pool.get('stock.quant')
            quant_ids = quant_obj.search(cr, uid, [('lot_id','=',rec.id),('product_id','=',rec.product_id.id),('location_id','in',int_loc_ids)])
            for quant in quant_obj.browse(cr, uid, quant_ids):
                res[rec.id] += quant.qty
        return res

    def _get_lot_id(self, cr, uid, ids, context=None):
        res = []
        for quant in self.browse(cr, uid, ids):
            res.append(quant.lot_id.id)
        return res

    _columns = {
        'lot_balance': fields.function(_compute_balance, type='float', string='Lot Qty on Hand',
            store={
#                     'stock.production.lot': (lambda self, cr, uid, ids, c={}: ids, None, 10),
                    'stock.quant': (_get_lot_id, None, 10),
                   })
    }

    def init(self, cr):
        # update lot_balance field when installing
        cr.execute("""
            update stock_production_lot lot
            set lot_balance =
                (select sum(qty)
                from stock_quant
                where lot_id = lot.id
                and product_id = lot.product_id
                and location_id in
                    (select id
                    from stock_location
                    where usage = 'internal'
                    )
                )
        """)

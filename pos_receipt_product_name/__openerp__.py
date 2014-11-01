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

{
    'name': 'POS Receipt Product Name',
    'version': '1.0',
    'author': 'Rooms For (Hong Kong) Ltd T/A OSCG',
    'website': 'http://www.open-asia.net',
    'category': 'Point of Sale',
    'sequence': 30,
    
    'depends': [
        "point_of_sale",
    ],
    'description': """
* Add a field called 'POS Product Name' to keep the product names presentable on POS receipt printed through PosBox. (As of 26 Oct 2014, PosBox does not handle double-byte Japanese characters)
* This module only handles the part that adds a field in product; receipt design is updated separately
    """,
    'data': [
        'product.xml',
     
    ],
    
    'installable': True,
   
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

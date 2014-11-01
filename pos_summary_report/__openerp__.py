# -*- encoding: utf-8 -*-
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
    'name': 'POS Daily Shop Sales Summary Report',
    'version': '1.0',
    'category' : "report",
    'description': """ 
* Adds a menu item 'Daily Shop Sales Report' which generates a summary of POS sales transactions for a date and a shop.
* The output is intended for printing to a receipt printer.
* In account.journal, there is a new field to keep report category info ('Cash', 'Receivable', etc.) for POS payment methods.
* In pos.category, there is a new field to indicate if the POS category is for 'deduction' in the summary report. 
    """,
    'author': 'Rooms For (Hong Kong) Ltd T/A OSCG',
    'depends': ['point_of_sale'],
    'init_xml': [],
    'update_xml': [
        'account_journal.xml',
        'pos_category.xml',
        'pos_summary_report.xml',
        'pos_summary_view.xml',
        'views/report_possummary.xml',
    ],
    'demo_xml': [],
    'installable': True,
    'active': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

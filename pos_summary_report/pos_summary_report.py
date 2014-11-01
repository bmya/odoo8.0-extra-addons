# -*- encoding: utf-8 -*-
#import os
#import time
#import base64
#from lxml import etree
#from StringIO import StringIO
#from os import listdir 
#from os.path import isfile, join, getmtime, basename
from openerp.osv import osv, fields
from datetime import datetime
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp
#import logging
#_logger = logging.getLogger(__name__)

class pos_summary_report(osv.osv_memory):
    _name = 'pos.summary.report'
    _description = u'Daily Shop Sales Report'
    _columns = {
        'name':fields.char('name'),
        'date':fields.date('Date'),
        'shop': fields.many2one('stock.location', 'Shop'),
        'header': fields.char('Header'),

        'gross_sales_cust': fields.integer(u'総売上'),
        'gross_sales_amt': fields.integer(u'総売上'),
        'vat_cust': fields.integer(u'消費税'),
        'vat_amt': fields.integer(u'消費税'),
        'other_deduction_cust': fields.integer(u'その他控除'),
        'other_deduction_amt': fields.integer(u'その他控除'),
        'net_sales_cust': fields.integer(u'純売上'),
        'net_sales_amt': fields.integer(u'純売上'),

        'sum_shopcash_cust': fields.integer(u'HaRuNe店現金'),
        'sum_shopcash_amt': fields.integer(u'HaRuNe店現金'),
        'sum_receivable_cust': fields.integer(u'売掛金'),
        'sum_receivable_amt': fields.integer(u'売掛金'),
        'sum_credit_cust': fields.integer(u'ｸﾚｼﾞｯﾄ(Square)'),
        'sum_credit_amt': fields.integer(u'ｸﾚｼﾞｯﾄ(Square)'),
        'sum_voucher_cust': fields.integer(u'商品券'),
        'sum_voucher_amt': fields.integer(u'商品券'),
        'sum_voucher_change_cust': fields.integer(u'商品券釣'),
        'sum_voucher_change_amt': fields.integer(u'商品券釣'),
        'sum_ecash_cust': fields.integer(u'電子ﾏﾈｰ'),
        'sum_ecash_amt': fields.integer(u'電子ﾏﾈｰ'),

        'sum_return_cust': fields.integer(u'取消・返品'),
        'sum_return_amt': fields.integer(u'取消・返品'),

        'base_cash': fields.integer(u'釣銭金額'),
        'cash_increase': fields.integer(u'現金増減額'),
        'cash_hand': fields.integer(u'現金残高'),

        'sequence': fields.char(u'精算回数'),
        'partner_id': fields.many2one('res.partner', 'User'),
    }
    _defaults = {
        'name': 'Daily Shop Sales Report',
        'date': fields.date.today(),
        'shop': lambda self,cr,uid,c: self.pool.get('res.users').browse(cr, uid, uid, c).pos_config and self.pool.get('res.users').browse(cr, uid, uid, c).pos_config.stock_location_id.id or False,
    }


    def _get_header(self, cr, uid, ids, shop, context=None):
        res = []
        pos_config_obj = self.pool.get('pos.config')
        pos_config_ids = []
        pos_config_ids += pos_config_obj.search(cr, uid, [('stock_location_id', '=', shop)], limit=1)
        for pos_config in pos_config_obj.browse(cr, uid, pos_config_ids, context=None):
            res = pos_config.receipt_header
        return res


    def _get_totals(self, cr, uid, ids, shop, date_start, date_end, context=None):
        res = {}
        params = [shop, date_start, date_end]

        # get gross sales
        cr.execute(
            "select sum(abs.amount), count(distinct po.id) "
            "from account_bank_statement_line abs, pos_order po "
            "where abs.pos_statement_id = po.id "
            "and po.location_id = %s "
            "and po.date_order >= %s "
            "and po.date_order <= %s", tuple(params)
            )
        res['gross_sales'] = cr.dictfetchone()

        # get vat
        cr.execute(
            "select sum(pol.price_subtotal_incl - pol.price_subtotal), count(distinct po.id) "
            "from pos_order_line pol, pos_order po "
            "where pol.order_id = po.id "
            "and po.location_id = %s "
            "and po.date_order >= %s "
            "and po.date_order <= %s", tuple(params)
            )
        res['vat'] = cr.dictfetchone()
        
        # get other deduction
        cr.execute(
            "select sum(pol.price_subtotal_incl), count(distinct po.id) "
            "from product_product pp, product_template pt, pos_category pc, pos_order_line pol, pos_order po "
            "where pol.order_id = po.id "
            "and po.location_id = %s "
            "and pol.product_id = pp.id "
            "and pp.product_tmpl_id = pt.id "
            "and pt.pos_categ_id = pc.id "
            "and pc.deduction = TRUE "
            "and po.date_order >= %s " 
            "and po.date_order <= %s", tuple(params)
            )
        res['other_deduction'] = cr.dictfetchone()

        return res


    def _get_breakdown(self, cr, uid, ids, shop, date_start, date_end, context=None):
        res = {}
        params = [shop, date_start, date_end]

        # get shop cash, receivable, credit, voucher and electronic cash data
        cr.execute(
            "select aj.summary_report_categ, sum(abs.amount), count(distinct po.id) "
            "from account_journal aj, account_bank_statement_line abs, pos_order po "
            "where abs.pos_statement_id = po.id "
            "and po.location_id = %s "
            "and abs.journal_id = aj.id "
            "and po.date_order >= %s "
            "and po.date_order <= %s "
            "group by aj.summary_report_categ", tuple(params)
            )
        for rec in cr.dictfetchall():
            res[rec['summary_report_categ']] = {}
            res[rec['summary_report_categ']]['sum'] = rec['sum']
            res[rec['summary_report_categ']]['count'] = rec['count']

        # get voucher change
        cr.execute(
            "select po.id "
            "from account_journal aj, account_bank_statement_line abs, pos_order po "
            "where abs.pos_statement_id = po.id "
            "and po.location_id = %s "
            "and abs.journal_id = aj.id "
            "and aj.summary_report_categ = 'voucher' "
            "and po.date_order >= %s "
            "and po.date_order <= %s", tuple(params)
            )
        ids = cr.dictfetchall() or []
        cust, amt = 0, 0
        pos_obj = self.pool.get('pos.order')
        for id in ids:
            pos_instance = pos_obj.browse(cr, uid, id.get('id'))
            cust += 1
            for line in pos_instance.statement_ids:
                if line.journal_id and line.journal_id.cash_control:
                    amt += line.amount
        res['sum_voucher_change'] = {}
        res['sum_voucher_change']['sum'] = amt
        res['sum_voucher_change']['count'] = cust
        
        # get returns
        cr.execute(
            "select sum(pol.price_subtotal_incl), count(distinct po.id) "
            "from pos_order_line pol, pos_order po "
            "where pol.order_id = po.id "
            "and po.location_id = %s "
            "and pol.price_subtotal_incl < 0 "
            "and po.date_order >= %s "
            "and po.date_order <= %s", tuple(params)
            )
        res['sum_return'] = cr.dictfetchone()
        
        return res


    def _get_session_info(self, cr, uid, ids, shop, date_start, date_end, context=None):
        res = {}
        session_obj = self.pool.get('pos.session')
        
        # get session name
        config_id = self.pool.get('pos.config').search(cr, uid, [('stock_location_id', '=', shop)], limit=1, order='name')
        session_id = session_obj.search(cr, uid, [('config_id','=',config_id), ('start_at','>=',date_start), ('start_at','<=',date_end)], limit=1, order='create_date desc')
        res['session_name'] = session_obj.read(cr, uid, session_id, ['name'])[0].get('name', '')
        
        # get opening balance
        res['opening_bal'] = 0
        config_ids = self.pool.get('pos.config').search(cr, uid, [('stock_location_id', '=', shop)])
        for id in config_ids:
            session_id = session_obj.search(cr, uid, [('config_id','=',id), ('start_at','>=',date_start), ('start_at','<=',date_end)], limit=1, order='create_date desc')
            res['opening_bal'] += session_obj.read(cr, uid, session_id, ['cash_register_balance_start'])[0].get('cash_register_balance_start')
        
        return res


    def query_report(self, cr, uid, ids, context=None):
        context = context or {}
        pos = self.browse(cr, uid, ids, context=context)
        date_start = "%s 00:00:00" % (pos.date)
        date_end = "%s 23:59:59" % (pos.date)
        if not pos.shop:
            raise osv.except_osv(_('Shop error!'),_('There is no shop available for you!'))
        
        # get header text
        header = self._get_header(cr, uid, ids, pos.shop.id, context=context)

        # get gross sales, vat, other deduction
        totals = self._get_totals(cr, uid, ids, pos.shop.id, date_start, date_end, context=context)
        gross_sales_cust = totals['gross_sales'].get('count', 0) 
        gross_sales_amt = totals['gross_sales'].get('sum', 0)
        vat_cust = totals['vat'].get('count', 0)
        vat_amt = totals['vat'].get('sum', 0)
        other_deduction_cust = totals['other_deduction'].get('count', 0) 
        if not totals['other_deduction'].get('sum', 0) == None:
            other_deduction_amt = totals['other_deduction'].get('sum', 0)
        else:
            other_deduction_amt = 0

        # get breakdown
        bd = self._get_breakdown(cr, uid, ids, pos.shop.id, date_start, date_end, context=context)
        sum_shopcash_cust = bd.get('shopcash', {}).get('count', 0)
        sum_shopcash_amt = bd.get('shopcash', {}).get('sum', 0)
        sum_receivable_cust = bd.get('receivable', {}).get('count', 0)
        sum_receivable_amt = bd.get('receivable', {}).get('sum', 0)
        sum_credit_cust = bd.get('credit', {}).get('count', 0)
        sum_credit_amt = bd.get('credit', {}).get('sum', 0)
        sum_voucher_cust = bd.get('voucher', {}).get('count', 0)
        sum_voucher_amt = bd.get('voucher', {}).get('sum', 0)
        sum_voucher_change_cust = bd.get('sum_voucher_change', {}).get('count', 0)
        sum_voucher_change_amt = bd.get('sum_voucher_change', {}).get('sum', 0)
        sum_ecash_cust = bd.get('ecash', {}).get('count', 0)
        sum_ecash_amt = bd.get('ecash', {}).get('sum', 0)
        sum_return_cust = bd.get('sum_return', {}).get('count', 0)
        sum_return_amt = bd.get('sum_return', {}).get('sum', 0)

        # get session info
        session_info = self._get_session_info(cr, uid, ids, pos.shop.id, date_start, date_end, context=context)
        session_name = session_info.get('session_name', '')
        opening_bal = session_info.get('opening_bal', 0)

        write_dic={
            'header': header,
            'gross_sales_cust': gross_sales_cust,
            'gross_sales_amt': gross_sales_amt,
            'vat_cust': vat_cust,
            'vat_amt': vat_amt,
            'other_deduction_cust': other_deduction_cust,
            'other_deduction_amt': other_deduction_amt,
            'net_sales_cust': gross_sales_cust,
            'net_sales_amt': gross_sales_amt - vat_amt - other_deduction_amt,
            'sum_shopcash_cust': sum_shopcash_cust,
            'sum_shopcash_amt': sum_shopcash_amt,
            'sum_receivable_cust': sum_receivable_cust,
            'sum_receivable_amt': sum_receivable_amt,
            'sum_credit_cust': sum_credit_cust,
            'sum_credit_amt': sum_credit_amt,
            'sum_voucher_cust': sum_voucher_cust,
            'sum_voucher_amt': sum_voucher_amt,
            'sum_voucher_change_cust': sum_voucher_change_cust,
            'sum_voucher_change_amt': sum_voucher_change_amt,
            'sum_ecash_cust': sum_ecash_cust,
            'sum_ecash_amt': sum_ecash_amt,
            'sum_return_cust': sum_return_cust,
            'sum_return_amt': sum_return_amt,
            'base_cash': opening_bal,
            'cash_increase': sum_shopcash_amt - sum_voucher_change_amt,
            'cash_hand': opening_bal + (sum_shopcash_amt - sum_voucher_change_amt),
            'sequence': session_name,
            #'partner_id': 1,
        }
        self.write(cr, uid, ids, write_dic)

        view_ref = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'pos_summary_report', 'pos_summary_report_query_form')
        view_id = view_ref and view_ref[1] or False,
        return {
            'type': 'ir.actions.act_window',
            'name': _('Daily Shop Sales Report'),
            'res_model': 'pos.summary.report',
            'res_id': ids[0],
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': view_id,
            'nodestroy': True,
            'context': context,
        }


    def print_report(self, cr, uid, ids, context=None):
        assert len(ids) == 1, 'This option should only be used for a single id at a time'
        return self.pool['report'].get_action(cr, uid, ids, 'pos_summary_report.report_possummary', context=context)

pos_summary_report()

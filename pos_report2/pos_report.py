# -*- encoding: utf-8 -*-
import os
import time
import base64
from lxml import etree
from StringIO import StringIO
from os import listdir 
from os.path import isfile, join, getmtime, basename
from openerp.osv import osv, fields
from lxml import etree
from datetime import datetime
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp
import logging
_logger = logging.getLogger(__name__)

class pos_report2(osv.osv_memory):
    _name = 'pos.report2'
    _description = u'Daily Shop Sales Report'

  
    _columns = {
        'name':fields.char('name'),
        'date':fields.date('Date'),
        'shop': fields.many2one('stock.location', 'Shop'),
        'header': fields.char('Header'),
#        'header': fields.function(_get_header, string='Header', type='char', store=True),

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
        param1 = [shop, date_start, date_end]

        # get gross sales
        cr.execute(
            "select sum(abs.amount), count(distinct po.id) "
            "from account_bank_statement_line abs, pos_order po "
            "where abs.pos_statement_id = po.id "
            "and po.location_id = %s "
            "and po.date_order >= %s "
            "and po.date_order <= %s", tuple(param1)
            )
        #res = cr.dictfetchall() or []
        res['gross_sales'] = cr.dictfetchone()

        # get vat
        cr.execute(
            "select sum(pol.price_subtotal_incl - pol.price_subtotal), count(distinct po.id) "
            "from pos_order_line pol, pos_order po "
            "where pol.order_id = po.id "
            "and po.location_id = %s "
            "and po.date_order >= %s "
            "and po.date_order <= %s", tuple(param1)
            )
        res['vat'] = cr.dictfetchone()
        
        # get other deduction
        categ_name = '値引き・送料'
        param2 = [shop, categ_name, date_start, date_end]
        cr.execute(
            "select sum(pol.price_subtotal_incl), count(distinct po.id) "
            "from product_product pp, product_template pt, pos_category pc, pos_order_line pol, pos_order po "
            "where pol.order_id = po.id "
            "and po.location_id = %s "
            "and pol.product_id = pp.id "
            "and pp.product_tmpl_id = pt.id "
            "and pt.pos_categ_id = pc.id "
            "and pc.name = %s "
            "and po.date_order >= %s " 
            "and po.date_order <= %s", tuple(param2)
            )
        res['other_deduction'] = cr.dictfetchone()

        return res


    def _get_breakdown(self, cr, uid, ids, shop, date_start, date_end, context=None):
        res = {}
        param1 = [shop, date_start, date_end]

        # get shop cash summary
        cr.execute(
            "select sum(abs.amount), count(distinct po.id) "
            "from account_journal aj, account_bank_statement_line abs, pos_order po "
            "where abs.pos_statement_id = po.id "
            "and po.location_id = %s "
            "and abs.journal_id = aj.id "
            "and aj.code = 'SHCS3' "
            "and po.date_order >= %s "
            "and po.date_order <= %s", tuple(param1)
            )
        res['sum_shopcash'] = cr.dictfetchone()

 
        
        return res


    def query_report2(self, cr, uid, ids, context=None):
        context = context or {}
        pos_obj = self.pool.get('pos.order')
        pos = self.browse(cr, uid, ids, context=context)
        date_start = "%s 00:00:00" % (pos.date)
        date_end = "%s 23:59:59" % (pos.date)
        if not pos.shop:
            raise osv.except_osv(_('Shop error!'),_('There is no shop available for you！'))
        
        # get header text
        header = self._get_header(cr, uid, ids, pos.shop.id, context=context)

        view_ref = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'pos_report2', 'pos_report_query_form')

        # get gross sales, vat, other deduction
        totals = self._get_totals(cr, uid, ids, pos.shop.id, date_start, date_end, context=context)
        gross_sales_cust, gross_sales_amt = totals['gross_sales'].get('count') or 0, totals['gross_sales'].get('sum') or 0
        vat_cust, vat_amt = totals['vat'].get('count') or 0, totals['vat'].get('sum') or 0
        other_deduction_cust, other_deduction_amt = totals['other_deduction'].get('count', 0) or 0, totals['other_deduction'].get('sum', 0) or 0


        
        sql_3="""select sum(abs.amount),count(distinct po.id) from account_journal aj,account_bank_statement_line abs,pos_order po where abs.pos_statement_id=po.id \
                and po.location_id=%s and abs.journal_id=aj.id and aj.code='SHCS3'and po.date_order>='%s' and po.date_order<='%s'"""%(pos.shop.id,date_start,date_end)
#        cr.execute(sql_3)
#        query3 = cr.dictfetchall() or []
        # get breakdown
        breakdown = self._get_breakdown(cr, uid, ids, pos.shop.id, date_start, date_end, context=context)
        sum_shopcash_cust, sum_shopcash_amt = breakdown['sum_shopcash'].get('count') or 0, breakdown['sum_shopcash'].get('sum') or 0
        
        sql_4=sql_3.replace('SHCS3','SHOT1')
        cr.execute(sql_4)
        query4 = cr.dictfetchall() or []
        sum_receivable_cust, sum_receivable_amt = query4[0].get('count',0) or 0, query4[0].get('sum',0) or 0

        sql_5=sql_3.replace('SHCS3','SHOT2')
        cr.execute(sql_5)
        query5 = cr.dictfetchall() or []
        sum_credit_cust, sum_credit_amt = query5[0].get('count',0) or 0 ,query5[0].get('sum',0) or 0

        sql_6=sql_3.replace('SHCS3','SHOT3')+' and abs.amount>=0'
        cr.execute(sql_6)
        query6 = cr.dictfetchall() or []
        sum_voucher_cust,sum_voucher_amt =query6[0].get('count',0) or 0,query6[0].get('sum',0) or 0
        
        sql_7="""select po.id from account_journal aj,account_bank_statement_line abs,pos_order po where abs.pos_statement_id=po.id \
                and po.location_id=%s and abs.journal_id=aj.id and aj.code='SHOT3'and po.date_order>='%s' and po.date_order<='%s'"""%(pos.shop.id,date_start,date_end)
        cr.execute(sql_7)
        query7 = cr.dictfetchall() or []
        sum_voucher_change_cust, sum_voucher_change_amt = 0, 0
        for query in query7:
            pos_instance=pos_obj.browse(cr,uid,query.get('id'))
            sum_voucher_change_cust+=1
            for line in pos_instance.statement_ids:
                if line.journal_id and line.journal_id.cash_control:
                    sum_voucher_change_amt += line.amount

        sql_8=sql_3.replace('SHCS3','SHOT4')
        cr.execute(sql_8)
        query8 = cr.dictfetchall() or []
        sum_ecash_cust, sum_ecash_amt = query8[0].get('count',0) or 0, query8[0].get('sum',0) or 0

        sql_9="""select sum(pol.price_subtotal_incl),count(distinct po.id) from pos_order_line pol,pos_order po where pol.order_id=po.id \
                and po.location_id=%s and pol.price_subtotal_incl<0 and po.date_order>='%s' and po.date_order<='%s'"""%(pos.shop.id,date_start,date_end)
        cr.execute(sql_9)
        query9 = cr.dictfetchall() or []
        sum_return_cust, sum_return_amt = query9[0].get('count',0) or 0, query9[0].get('sum',0) or 0

        sql_10="""select ps.id from pos_session ps,pos_config pc where ps.start_at>='%s' and ps.start_at<='%s' and config_id=pc.id \
         and pc.stock_location_id=%s order by ps.create_date"""%(date_start,date_end,pos.shop.id)
        cr.execute(sql_10)
        #query10===[{'id': 6}, {'id': 7}]
        query10 = cr.dictfetchall() or []
        read_dic={}
        if query10:
            search_id=query10[0]['id']
            read_dic=self.pool.get('pos.session').read(cr,uid,search_id,{'cash_register_balance_start','cash_register_total_entry_encoding','cash_register_balance_end','name'})

        write_dic={
            'header':header,
            'gross_sales_cust':gross_sales_cust,
            'gross_sales_amt':gross_sales_amt,
            'vat_cust':vat_cust,
            'vat_amt':vat_amt,
            'other_deduction_cust':other_deduction_cust,
            'other_deduction_amt':other_deduction_amt,
            'net_sales_cust':gross_sales_cust,
            'net_sales_amt': gross_sales_amt - vat_amt - other_deduction_amt,
            'sum_shopcash_cust':sum_shopcash_cust,
            'sum_shopcash_amt':sum_shopcash_amt,
            'sum_receivable_cust':sum_receivable_cust,
            'sum_receivable_amt':sum_receivable_amt,
            'sum_credit_cust':sum_credit_cust,
            'sum_credit_amt':sum_credit_amt,
            'sum_voucher_cust':sum_voucher_cust,
            'sum_voucher_amt':sum_voucher_amt,
            'sum_voucher_change_cust':sum_voucher_change_cust,
            'sum_voucher_change_amt':sum_voucher_change_amt,
            'sum_ecash_cust':sum_ecash_cust,
            'sum_ecash_amt':sum_ecash_amt,
            'sum_return_cust':sum_return_cust,
            'sum_return_amt':sum_return_amt,
            'base_cash':read_dic.get('cash_register_balance_start') or 0,
            'cash_increase':sum_shopcash_amt - sum_voucher_change_amt,
            'cash_hand':(read_dic.get('cash_register_balance_start') or 0) + (sum_shopcash_amt - sum_voucher_change_amt),
            'sequence':read_dic.get('name') or '',
            #'partner_id': 1,
        }
        self.write(cr,uid,ids,write_dic)
        view_id = view_ref and view_ref[1] or False,
        return {
            'type': 'ir.actions.act_window',
            'name': _('Daily Shop Sales Report'),
            'res_model': 'pos.report2',
            'res_id': ids[0],
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': view_id,
            'nodestroy': True,
            'context':context,
        }
            #'target': 'inlineview',
            #'target': 'inline',

    def query_report3(self, cr, uid, ids, context=None):
        '''
        This function prints the POS summary
        '''
        assert len(ids) == 1, 'This option should only be used for a single id at a time'
        return self.pool['report'].get_action(cr, uid, ids, 'pos_report2.report_possummary', context=context)

pos_report2()

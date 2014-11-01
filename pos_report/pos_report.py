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

class pos_report(osv.osv_memory):
    _name = 'pos.report'
    _description = u'Daily Shop Sales Report'
    _columns = {
        'name':fields.char('name'),
        'text1':fields.char('text'),
        'text2':fields.char('text'),
        'text3':fields.char('text'),
        'date':fields.date('Date'),
        'shop': fields.many2one('stock.location', 'Shop'),
        'header': fields.char('Header'),
        'phone': fields.char('Tel',size=20),
        'net': fields.char('Net'),
        'total_with_tax': fields.integer(u'総売上'),
        'total_with_tax2': fields.integer(u'総売上'),
        'tax': fields.integer(u'消費税'),
        'tax2': fields.integer(u'消費税'),
        'consum_delivery': fields.integer(u'その他控除'),
        'consum_delivery2': fields.integer(u'その他控除'),
        'total_without_tax': fields.integer(u'純売上'),
        'total_without_tax2': fields.integer(u'純売上'),
        'total_cash': fields.integer(u'HaRuNe店現金'),
        'total_cash2': fields.integer(u'HaRuNe店現金'),
        'total_invoice': fields.integer(u'売掛金'),
        'total_invoice2': fields.integer(u'売掛金'),
        'total_card': fields.integer(u'ｸﾚｼﾞｯﾄ(Square)'),
        'total_card2': fields.integer(u'ｸﾚｼﾞｯﾄ(Square)'),
        'total_ticket': fields.integer(u'商品券'),
        'total_ticket2': fields.integer(u'商品券'),
        'total_virtual_currency': fields.integer(u'商品券釣'),
        'total_virtual_currency2': fields.integer(u'商品券釣'),
        'total_rebate': fields.integer(u'電子ﾏﾈｰ'),
        'total_rebate2': fields.integer(u'電子ﾏﾈｰ'),
        'total_return': fields.integer(u'取消・返品'),
        'total_return2': fields.integer(u'取消・返品'),
        'base_cash': fields.integer(u'釣銭金額'),
        'cash_increase': fields.integer(u'現金増減額'),
        'cash_hand': fields.integer(u'現金残高'),
        'sequence': fields.char(u'精算回数'),
    }
    _defaults = {
        'name': 'Daily Shop Sales Report',
        'phone': 'Tel: 050-6860-4792',
        'net': 'facebook.com/yakigashiyachinriu',
        'date': fields.date.today(),
        'shop': lambda self,cr,uid,c: self.pool.get('res.users').browse(cr, uid, uid, c).pos_config and self.pool.get('res.users').browse(cr, uid, uid, c).pos_config.stock_location_id.id or False,
        'text1':'**************************************************',
        'text2':'ﾆｯﾎﾟｳ',
        'text3':'**************************************************',
    }
    
    def query_report(self, cr, uid, ids, context=None):
        context=context or {}
        pos_obj=self.pool.get('pos.order')
        pos=self.browse(cr, uid, ids, context=context)
        date_start = "%s 00:00:00" % (pos.date)
        date_end = "%s 23:59:59" % (pos.date)
        if not pos.shop:
            raise osv.except_osv(_('Shop error!'),_('There is no shop available for you！'))
        header=''
        sql_0="""select receipt_header from pos_config where stock_location_id =%s and receipt_header is not null"""%(pos.shop.id)
        cr.execute(sql_0)
        query0 = cr.dictfetchall() or []
        header=query0[0].get('receipt_header') or ''
        view_ref = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'pos_report', 'pos_report_query_form')
        sql_1="""select sum(abs.amount),count(distinct po.id) from account_bank_statement_line abs,pos_order po where abs.pos_statement_id=po.id \
                and po.location_id=%s and po.date_order>='%s' and po.date_order<='%s'"""%(pos.shop.id,date_start,date_end)
        cr.execute(sql_1)
        query1 = cr.dictfetchall() or []
        #query1==[{'count': 15L, 'sum': 62814.0}]
        total_with_tax,total_with_tax2=query1[0].get('count') or 0,query1[0].get('sum') or 0
        
        sql_2="""select sum(pol.price_subtotal_incl - pol.price_subtotal),count(distinct po.id) from pos_order_line pol,pos_order po where pol.order_id=po.id \
                and po.location_id=%s and po.date_order>='%s' and po.date_order<='%s'"""%(pos.shop.id,date_start,date_end)
        cr.execute(sql_2)
        query2 = cr.dictfetchall() or []
        tax,tax2=query2[0].get('count') or 0,query2[0].get('sum') or 0
        categ_name='測試'
        sql_11="""select sum(pol.price_subtotal_incl),count(distinct po.id) from product_product pp,product_template pt,pos_category pc\
                  ,pos_order_line pol,pos_order po where pol.order_id=po.id and po.location_id=%s and pol.product_id=pp.id \
                  and pp.product_tmpl_id=pt.id and pt.pos_categ_id=pc.id and pc.name ='%s' and po.date_order>='%s' and po.date_order<='%s'"""%(pos.shop.id,categ_name,date_start,date_end)
        cr.execute(sql_11)
        query11 = cr.dictfetchall() or []
        consum_delivery,consum_delivery2=query11[0].get('count',0) or 0,query11[0].get('sum',0) or 0
        total_without_tax2=total_with_tax2-tax2-consum_delivery2
        sql_3="""select sum(abs.amount),count(distinct po.id) from account_journal aj,account_bank_statement_line abs,pos_order po where abs.pos_statement_id=po.id \
                and po.location_id=%s and abs.journal_id=aj.id and aj.code='SHCS3'and po.date_order>='%s' and po.date_order<='%s'"""%(pos.shop.id,date_start,date_end)
        cr.execute(sql_3)
        query3 = cr.dictfetchall() or []
        total_cash,total_cash2=query3[0].get('count') or 0 ,query3[0].get('sum') or 0
        sql_4=sql_3.replace('SHCS3','SHOT1')
        cr.execute(sql_4)
        query4 = cr.dictfetchall() or []
        total_invoice,total_invoice2=query4[0].get('count',0) or 0,query4[0].get('sum',0) or 0
        sql_5=sql_3.replace('SHCS3','SHOT2')
        cr.execute(sql_5)
        query5 = cr.dictfetchall() or []
        total_card,total_card2=query5[0].get('count',0) or 0 ,query5[0].get('sum',0) or 0
        sql_6=sql_3.replace('SHCS3','SHOT3')+' and abs.amount>=0'
        cr.execute(sql_6)
        query6 = cr.dictfetchall() or []
        total_ticket,total_ticket2=query6[0].get('count',0) or 0,query6[0].get('sum',0) or 0
        
        sql_7="""select po.id from account_journal aj,account_bank_statement_line abs,pos_order po where abs.pos_statement_id=po.id \
                and po.location_id=%s and abs.journal_id=aj.id and aj.code='SHOT3'and po.date_order>='%s' and po.date_order<='%s'"""%(pos.shop.id,date_start,date_end)
        cr.execute(sql_7)
        query7 = cr.dictfetchall() or []
        total_virtual_currency,total_virtual_currency2=0,0
        for query in query7:
            pos_instance=pos_obj.browse(cr,uid,query.get('id'))
            total_virtual_currency+=1
            for line in pos_instance.statement_ids:
                if line.journal_id and line.journal_id.cash_control:
                    total_virtual_currency2+=line.amount
        sql_8=sql_3.replace('SHCS3','SHOT4')
        cr.execute(sql_8)
        query8 = cr.dictfetchall() or []
        total_rebate,total_rebate2=query8[0].get('count',0) or 0,query8[0].get('sum',0) or 0
        sql_9="""select sum(pol.price_subtotal_incl),count(distinct po.id) from pos_order_line pol,pos_order po where pol.order_id=po.id \
                and po.location_id=%s and pol.price_subtotal_incl<0 and po.date_order>='%s' and po.date_order<='%s'"""%(pos.shop.id,date_start,date_end)
        cr.execute(sql_9)
        query9 = cr.dictfetchall() or []
        total_return,total_return2=query9[0].get('count',0) or 0,query9[0].get('sum',0) or 0
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
            'total_with_tax2':total_with_tax2,
            'total_with_tax':total_with_tax,
            'tax2':tax2,
            'tax':tax,
            'consum_delivery':consum_delivery,
            'consum_delivery2':consum_delivery2,
            'total_without_tax2':total_without_tax2,
            'total_without_tax':total_with_tax,
            'total_cash':total_cash,
            'total_cash2':total_cash2,
            'total_invoice':total_invoice,
            'total_invoice2':total_invoice2,
            'total_card':total_card,
            'total_card2':total_card2,
            'total_ticket':total_ticket,
            'total_ticket2':total_ticket2,
            'total_virtual_currency':total_virtual_currency,
            'total_virtual_currency2':total_virtual_currency2,
            'total_rebate':total_rebate,
            'total_rebate2':total_rebate2,
            'total_return':total_return,
            'total_return2':total_return2,
            'base_cash':read_dic.get('cash_register_balance_start') or 0,
            #'cash_increase':read_dic.get('cash_register_total_entry_encoding') or 0,
            'cash_increase':total_cash2 - total_virtual_currency2,
            #'cash_hand':read_dic.get('cash_register_balance_end') or 0,
            'cash_hand':(read_dic.get('cash_register_balance_start') or 0) + (total_cash2 - total_virtual_currency2),
            #'sequence':(read_dic.get('name') or '').replace('/','').replace('POS',''),
            'sequence':read_dic.get('name') or '',
        }
        self.write(cr,uid,ids,write_dic)
        view_id = view_ref and view_ref[1] or False,
        return {
            'type': 'ir.actions.act_window',
            'name': _('Daily Shop Sales Report'),
            'res_model': 'pos.report',
            'res_id': ids[0],
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': view_id,
            'nodestroy': True,
            'context':context,
        }
            #'target': 'inlineview',
            #'target': 'inline',
pos_report()

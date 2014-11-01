# -*- encoding: utf-8 -*-

{
    'name': 'POS Report 2',
    'version': '1.0',
    "category" : "report",
    'description': """ 
    POS statistics report
    """,
    'author': 'OSCG',
    'depends': ['point_of_sale'],
    'init_xml': [],
    'update_xml': [
        'pos_report.xml',
        'pos_view.xml',
        'views/report_possummary.xml',
    ],
    'demo_xml': [],
    'installable': True,
    'active': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

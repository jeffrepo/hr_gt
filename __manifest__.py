# -*- coding: utf-8 -*-

{
    'name': 'hr_gt',
    'version': '1.0',
    'category': 'Hidden',
    'sequence': 6,
    'summary': 'Recursos humanos para Gt',
    'description': """

""",
    'depends': ['hr','hr_contract','hr_payroll','hr_work_entry_contract_enterprise'],
    'data': [
        'views/hr_views.xml',
        'views/report.xml',
        'views/hr_gt_views.xml',
        'data/data.xml',
        'views/recibo_pago.xml',
        'views/hr_contract_views.xml',
        'views/res_company_views.xml',
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'auto_install': False,
}

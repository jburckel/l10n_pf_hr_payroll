# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'French Polynesia Payroll',
    'version': '18.0.1.0.0',
    'category': 'Localization',
    'summary': 'French Polynesia payroll localization',
    'author': 'Your Company',
    'website': 'https://www.yourcompany.com',
    'depends': ['hr_payroll', 'l10n_pf', 'hr_holidays'],
    'description': """
French Polynesia Payroll Rules.
=====================

    - Configuration of hr_payroll for French Polynesia localization
    - Salary rules specific to French Polynesia legislation
    - Leave management integration
    - Payslip reports in French
    """,
    'data': [
        'views/l10n_pf_hr_payroll_view.xml',
        'views/res_config_settings_views.xml',
        'report/l10n_pf_hr_payroll_report.xml',
	    'report/report_fiche_paye.xml'
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'LGPL-3',
}

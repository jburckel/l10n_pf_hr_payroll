# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'French Polynesia Payroll',
    'category': 'Localization',
    'depends': ['payroll', 'l10n_pf', 'hr_holidays'],
    'description': """
French Polynesia Payroll Rules.
=====================

    - Configuration of hr_payroll for French Polynesia localization
    """,
    'data': [
        'views/l10n_pf_hr_payroll_view.xml',
        'views/res_config_settings_views.xml',
        'report/l10n_pf_hr_payroll_report.xml',
	    'report/report_fiche_paye.xml'
    ],
}

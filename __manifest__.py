# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'French Polynesia Payroll',
    'category': 'Localization',
    'depends': ['hr_payroll', 'l10n_pf'],
    'description': """
French Payroll Rules.
=====================

    - Configuration of hr_payroll for French Polynesia localization
    - New payslip report

TODO:
-----
    - Integration with holidays module for deduction and allowance
    - Integration with hr_payroll_account for the automatic account_move_line
      creation from the payslip
    - Continue to integrate the contribution. Only the main contribution are
      currently implemented
    - Remake the report under webkit
    - The payslip.line with appears_in_payslip = False should appears in the
      payslip interface, but not in the payslip report
    """,
    'data': [
        'views/l10n_pf_hr_payroll_view.xml',
        'report/l10n_pf_hr_payroll_report.xml',
	'report/report_fiche_paye.xml',
    ],
}

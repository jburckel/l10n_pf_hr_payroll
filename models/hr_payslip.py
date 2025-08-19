# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, tools, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)



class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    payment_mode = fields.Char(string='Mode de paiement')

    acompte = fields.Float(
        string='Acomptes du mois',
        readonly=True,
        readonly_state='draft',
        default=0,
    )

    heure_absence = fields.Float(
        string='Heures d\'absence',
        readonly=True,
        readonly_state='draft',
        default=0,
    )

    heure_comp = fields.Float(
        string='Heures complémentaires',
        readonly=True,
        readonly_state='draft',
        default=0,
    )

    heure_sup_125 = fields.Float(
        string='Heures supp. 125%',
        readonly=True,
        readonly_state='draft',
        default=0,
    )

    heure_sup_150 = fields.Float(
        string='Heures supp. 150%',
        readonly=True,
        readonly_state='draft',
        default=0,
    )

    heure_sup_165 = fields.Float(
        string='Heures supp. 165%',
        readonly=True,
        readonly_state='draft',
        default=0,
    )

    heure_sup_175 = fields.Float(
        string='Heures supp. 175%',
        readonly=True,
        readonly_state='draft',
        default=0,
    )

    heure_sup_200 = fields.Float(
        string='Heures supp. 200%',
        readonly=True,
        readonly_state='draft',
        default=0,
    )

    @api.onchange('employee_id')
    def get_contract_values(self):
        if not self.env.context.get("noUpdate"):
            pay = self
            contract = self.env['hr.contract'].search(
                [('state', '!=', 'close'), ('employee_id', '=', pay.employee_id.id)],
                limit=1)
            if contract:
                self.contract_id = contract[0]
                # self.struct_id = contract[0].struct_id
                self.conge_acquis = contract[0].conge_mensuel
                self.anciennete = contract[0].taux_anciennete
                self.heure_contrat = contract[0].heure_mensuelle
                self.wage = contract[0].wage
                self.taux_horaire = contract[0].taux_horaire
                self.indemnite_conge_paye = contract[0].indemnite_conge_paye
                self.get_auto_holidays()
                self.compute_holidays()

    conge_acquis = fields.Float(
        string='Congé acquis (j)',
        readonly=True,
        readonly_state='draft',
        default=0,
    )

    attribution_conge_id = fields.Many2one(
        'hr.leave.allocation',
        string='Attribution mensuelle de congé enregistrée',
        readonly=True
    )

    conge_restant = fields.Float(
        'Congé restant (j)',
        readonly=True,
        default=0
    )

    conge_pris = fields.Float(
        string='Congé pris (j)',
        readonly=True,
        readonly_state='draft',
        default=0,
    )

    heure_contrat = fields.Float(
        string='Heures du contrat',
        readonly=True,
        default=0
    )

    anciennete = fields.Float(
        string='Ancienneté',
        readonly=True,
        default=0
    )

    wage = fields.Monetary(
        string='Salaire',
        readonly=True,
        default=0
    )

    currency_id = fields.Many2one(
        string="Currency",
        related='company_id.currency_id',
        readonly=True
    )

    taux_horaire = fields.Float(
        string='Taux horaire',
        readonly=True,
        default=0
    )

    indemnite_conge_paye = fields.Float(
        string='Indemnité de congé payé',
        readonly=True,
        readonly_state='draft',
        default=0,
    )

    conge_enregistre_ids = fields.Many2many(
        'hr.leave',
        string='Congés pris en compte',
        readonly=True,
        readonly_state='draft',
    )
    @api.onchange('conge_enregistre_ids')
    def _update_conge_enregistre_ids(self):
        conge_pris = 0
        for leave in self.conge_enregistre_ids:
            conge_pris += leave.number_of_days
        self.conge_pris = conge_pris
        self.compute_holidays()

    def _get_conge_domain(self):
        return [('employee_id', '=', self.employee_id), ('company_id', '=', self.company_id)]
    
    def _get_payslip_line_total(self, amount, quantity, rate, rule):
        self.ensure_one()
        return round(super()._get_payslip_line_total(amount, quantity, rate, rule))

    @api.model
    def create(self, values):
        record = super(HrPayslip, self).create(values)
        record.get_contract_values()
        return record


    @api.onchange('conge_acquis')
    def compute_conge_acquis(self):
        self.compute_holidays()

    @api.model
    def get_worked_day_lines(self, contracts, date_from, date_to):
        return []

    def _get_parameter_holiday_type(self):
        holiday = self.env['ir.config_parameter'].get_param('l10n_pf_hr_payroll.holiday_code')
        if not holiday:
            raise ValidationError("Veuillez configurer le type de congés à utiliser.")
        return int(holiday)

    def _get_sum_allocation(self):
        if self.employee_id:
            self._cr.execute("""
                SELECT
                    sum(number_of_days) AS days
                FROM hr_leave_allocation
                WHERE
                    state='validate' AND 
                    employee_id=%s AND
                    holiday_status_id=%s
            """, (self.employee_id.id, self._get_parameter_holiday_type()))
            result = self._cr.dictfetchall()
            return result[0]['days'] if (len(result) and result[0]['days'] is not None) else 0
        return 0

    def _get_sum_leave(self, validated=True):
        if self.employee_id:
            sql_query = ("""
                SELECT
                    sum(number_of_days) AS days
                FROM hr_leave
                WHERE
                    state='validate' AND 
                    employee_id={0} AND
                    holiday_status_id={1}
            """).format(self.employee_id.id, self._get_parameter_holiday_type())
            if validated is not None:
                validated_string = 'True' if validated else 'False'
                sql_query += ("""
                        AND payslip_status={0}
                """).format(validated_string)
            self._cr.execute(sql_query)
            result = self._cr.dictfetchall()
            return result[0]['days'] if (len(result) and result[0]['days'] is not None) else 0
        return 0

    def get_auto_holidays(self):
        for payslip in self:
            leaves_db = self.env['hr.leave'].search(
                [
                    ('employee_id', '=', payslip.employee_id.id),
                    ('payslip_status', '=', False),
                    ('holiday_status_id', '=', self._get_parameter_holiday_type())
                ]
            )
            payslip.write({'conge_enregistre_ids': [(6, 0, [])]})
            conge_pris = 0
            for leave in leaves_db:
                if leave.holiday_status_id.id == self._get_parameter_holiday_type():
                    conge_pris += leave.number_of_days
                    payslip.write({'conge_enregistre_ids': [(4, leave.id)]})
            payslip.conge_pris = conge_pris

    def compute_holidays(self):
        for payslip in self:
            conge_initial = payslip._get_sum_allocation() - payslip._get_sum_leave(validated=True)
            payslip.conge_restant = conge_initial + payslip.conge_acquis - payslip.conge_pris

    def action_compute_holidays(self):
        self.get_auto_holidays()
        self.compute_holidays()

    def action_payslip_done(self):
        if self.env['ir.config_parameter'].get_param('l10n_pf_hr_payroll.add_leave_attribution_when_done'):
            self.add_holiday_allocation()
        if self.env['ir.config_parameter'].get_param('l10n_pf_hr_payroll.validate_leave_when_done'):
            self.close_saved_leaves()
        return self.with_context(noUpdate=True).write({"state": "done"})

    def add_holiday_allocation(self):
        if self.conge_acquis > 0:
            allocation = self.env['hr.leave.allocation']
            description = "Attribution liée au bulletin {0}".format(self.name)
            self.attribution_conge_id = allocation.create(
                {
                    'name': description,
                    'employee_id': self.employee_id.id,
                    'number_of_days': self.conge_acquis,
                    'state': 'validate',
                    'holiday_status_id': self._get_parameter_holiday_type(),
                    'allocation_type': 'regular',
                    'holiday_type': 'employee'
                }
            )

    def close_saved_leaves(self):
        for leave in self.conge_enregistre_ids:
            leave.write({'payslip_status': True})

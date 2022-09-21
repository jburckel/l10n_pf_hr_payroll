# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, tools, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


# These classes are used in the _get_payslip_lines() method
class BrowsableObject(object):
    def __init__(self, employee_id, vals_dict, env):
        self.employee_id = employee_id
        self.dict = vals_dict
        self.env = env

    def __getattr__(self, attr):
        return attr in self.dict and self.dict.__getitem__(attr) or 0.0


class InputLine(BrowsableObject):
    """a class that will be used into the python code, mainly for
    usability purposes"""

    def sum(self, code, from_date, to_date=None):
        if to_date is None:
            to_date = fields.Date.today()
        self.env.cr.execute(
            """
            SELECT sum(amount) as sum
            FROM hr_payslip as hp, hr_payslip_input as pi
            WHERE hp.employee_id = %s AND hp.state = 'done'
            AND hp.date_from >= %s AND hp.date_to <= %s
            AND hp.id = pi.payslip_id AND pi.code = %s""",
            (self.employee_id, from_date, to_date, code),
        )
        return self.env.cr.fetchone()[0] or 0.0


class WorkedDays(BrowsableObject):
    """a class that will be used into the python code, mainly for
    usability purposes"""

    def _sum(self, code, from_date, to_date=None):
        if to_date is None:
            to_date = fields.Date.today()
        self.env.cr.execute(
            """
            SELECT sum(number_of_days) as number_of_days,
             sum(number_of_hours) as number_of_hours
            FROM hr_payslip as hp, hr_payslip_worked_days as pi
            WHERE hp.employee_id = %s AND hp.state = 'done'
            AND hp.date_from >= %s AND hp.date_to <= %s
            AND hp.id = pi.payslip_id AND pi.code = %s""",
            (self.employee_id, from_date, to_date, code),
        )
        return self.env.cr.fetchone()

    def sum(self, code, from_date, to_date=None):
        res = self._sum(code, from_date, to_date)
        return res and res[0] or 0.0

    def sum_hours(self, code, from_date, to_date=None):
        res = self._sum(code, from_date, to_date)
        return res and res[1] or 0.0


class Payslips(BrowsableObject):
    """a class that will be used into the python code, mainly for
    usability purposes"""

    def sum(self, code, from_date, to_date=None):
        if to_date is None:
            to_date = fields.Date.today()
        self.env.cr.execute(
            """SELECT sum(case when hp.credit_note = False then
            (pl.total) else (-pl.total) end)
                    FROM hr_payslip as hp, hr_payslip_line as pl
                    WHERE hp.employee_id = %s AND hp.state = 'done'
                    AND hp.date_from >= %s AND hp.date_to <= %s AND
                     hp.id = pl.slip_id AND pl.code = %s""",
            (self.employee_id, from_date, to_date, code),
        )
        res = self.env.cr.fetchone()
        return res and res[0] or 0.0





class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    payment_mode = fields.Char(string='Mode de paiement')

    acompte = fields.Float(
        string='Acomptes du mois',
        readonly=True,
        default=0,
        states={"draft": [("readonly", False)]}
    )

    heure_absence = fields.Float(
        string='Heures d\'absence',
        readonly=True,
        default=0,
        states={"draft": [("readonly", False)]}
    )

    heure_comp = fields.Float(
        string='Heures complémentaires',
        readonly=True,
        default=0,
        states={"draft": [("readonly", False)]}
    )

    heure_sup_125 = fields.Float(
        string='Heures supp. 125%',
        readonly=True,
        default=0,
        states={"draft": [("readonly", False)]}
    )

    heure_sup_150 = fields.Float(
        string='Heures supp. 150%',
        readonly=True,
        default=0,
        states={"draft": [("readonly", False)]}
    )

    heure_sup_165 = fields.Float(
        string='Heures supp. 165%',
        readonly=True,
        default=0,
        states={"draft": [("readonly", False)]}
    )

    heure_sup_175 = fields.Float(
        string='Heures supp. 175%',
        readonly=True,
        default=0,
        states={"draft": [("readonly", False)]}
    )

    heure_sup_200 = fields.Float(
        string='Heures supp. 200%',
        readonly=True,
        default=0,
        states={"draft": [("readonly", False)]}
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
                self.struct_id = contract[0].struct_id
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
        default=0,
        states={"draft": [("readonly", False)]}
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
        default=0,
        states = {"draft": [("readonly", False)]}
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
        default=0,
        states={"draft": [("readonly", False)]}
    )

    conge_enregistre_ids = fields.Many2many(
        'hr.leave',
        string='Congés pris en compte',
        readonly=True,
        states={"draft": [("readonly", False)]}
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

    @api.model
    def create(self, values):
        record = super(HrPayslip, self).create(values)
        record.get_contract_values()
        return record

    @api.model
    def _get_payslip_lines(self, contract_ids, payslip_id):
        """
        Need to add round when computing category. Go to line 246
        :param contract_ids:
        :param payslip_id:
        :return:
        """

        def _sum_salary_rule_category(localdict, category, amount):
            if category.parent_id:
                localdict = _sum_salary_rule_category(
                    localdict, category.parent_id, amount
                )

            if category.code in localdict["categories"].dict:
                localdict["categories"].dict[category.code] += amount
            else:
                localdict["categories"].dict[category.code] = amount

            return localdict

        # we keep a dict with the result because a value can be overwritten by
        # another rule with the same code
        result_dict = {}
        rules_dict = {}
        worked_days_dict = {}
        inputs_dict = {}
        blacklist = []
        payslip = self.env["hr.payslip"].browse(payslip_id)
        for worked_days_line in payslip.worked_days_line_ids:
            worked_days_dict[worked_days_line.code] = worked_days_line
        for input_line in payslip.input_line_ids:
            inputs_dict[input_line.code] = input_line

        categories = BrowsableObject(payslip.employee_id.id, {}, self.env)
        inputs = InputLine(payslip.employee_id.id, inputs_dict, self.env)
        worked_days = WorkedDays(payslip.employee_id.id, worked_days_dict, self.env)
        payslips = Payslips(payslip.employee_id.id, payslip, self.env)
        rules = BrowsableObject(payslip.employee_id.id, rules_dict, self.env)

        baselocaldict = {
            "categories": categories,
            "rules": rules,
            "payslip": payslips,
            "worked_days": worked_days,
            "inputs": inputs,
        }
        # get the ids of the structures on the contracts and their parent id
        # as well
        contracts = self.env["hr.contract"].browse(contract_ids)
        if len(contracts) == 1 and payslip.struct_id:
            structure_ids = list(set(payslip.struct_id._get_parent_structure().ids))
        else:
            structure_ids = contracts.get_all_structures()
        # get the rules of the structure and thier children
        rule_ids = (
            self.env["hr.payroll.structure"].browse(structure_ids).get_all_rules()
        )
        # run the rules by sequence
        sorted_rule_ids = [id for id, sequence in sorted(rule_ids, key=lambda x: x[1])]
        sorted_rules = self.env["hr.salary.rule"].browse(sorted_rule_ids)

        for contract in contracts:
            employee = contract.employee_id
            localdict = dict(baselocaldict, employee=employee, contract=contract)
            for rule in sorted_rules:
                key = rule.code + "-" + str(contract.id)
                localdict["result"] = None
                localdict["result_qty"] = 1.0
                localdict["result_rate"] = 100
                # check if the rule can be applied
                if rule._satisfy_condition(localdict) and rule.id not in blacklist:
                    # compute the amount of the rule
                    amount, qty, rate = rule._compute_rule(localdict)
                    # check if there is already a rule computed with that code
                    previous_amount = (
                            rule.code in localdict and localdict[rule.code] or 0.0
                    )
                    # set/overwrite the amount computed for this rule in the
                    # localdict
                    ######## Only changes for pf payroll Module ########
                    tot_rule = round(amount * qty * rate / 100.0)
                    localdict[rule.code] = tot_rule
                    rules_dict[rule.code] = rule
                    # sum the amount for its salary category
                    localdict = _sum_salary_rule_category(
                        localdict, rule.category_id, tot_rule - previous_amount
                    )
                    # create/overwrite the rule in the temporary results
                    result_dict[key] = {
                        "salary_rule_id": rule.id,
                        "contract_id": contract.id,
                        "name": rule.name,
                        "code": rule.code,
                        "category_id": rule.category_id.id,
                        "sequence": rule.sequence,
                        "appears_on_payslip": rule.appears_on_payslip,
                        "condition_select": rule.condition_select,
                        "condition_python": rule.condition_python,
                        "condition_range": rule.condition_range,
                        "condition_range_min": rule.condition_range_min,
                        "condition_range_max": rule.condition_range_max,
                        "amount_select": rule.amount_select,
                        "amount_fix": rule.amount_fix,
                        "amount_python_compute": rule.amount_python_compute,
                        "amount_percentage": rule.amount_percentage,
                        "amount_percentage_base": rule.amount_percentage_base,
                        "register_id": rule.register_id.id,
                        "amount": amount,
                        "employee_id": contract.employee_id.id,
                        "quantity": qty,
                        "rate": rate,
                    }
                else:
                    # blacklist this rule and its children
                    blacklist += [id for id, seq in rule._recursive_search_of_rules()]

        return list(result_dict.values())

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

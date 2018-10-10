# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, tools, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError, ValidationError
from odoo.tools.safe_eval import safe_eval
from datetime import datetime, timedelta, date
from dateutil import relativedelta
from math import floor

class customHRContract(models.Model):
     _inherit = 'hr.contract'

     heure_mensuelle = fields.Integer('Horaire mensuel',default=169)
     taux_horaire = fields.Float('Taux horaire')
     conge_mensuel = fields.Float(string='Congés mensuels attribués',default=2.5)
     indemnite_conge_paye = fields.Float('Indemnité de congé payé (par jour)')
     taux_anciennete = fields.Float('Anciennete')
     jours_travailles = fields.Float('Nombre de jours travaillés', default=5)

     @api.onchange('wage', 'heure_mensuelle')
     def update_field(self):
          if self.heure_mensuelle > 0:
               self.taux_horaire = self.wage / self.heure_mensuelle

     def compute_anciennete(self,date_start):
          today = date.today()
          delta = today - fields.Date.from_string(date_start)
          anciennete = floor(delta.days / 365.25)
          if anciennete < 3:
               anciennete = 0
          elif anciennete > 25:
               anciennete = 25
          return anciennete

     @api.onchange('date_start')
     def update_field_anciennete(self):
          self.taux_anciennete = self.compute_anciennete(self.date_start)

     def update_anciennete(self):
          contracts = self.search([('state', '!=', 'close')])
          for contract in contracts:
               anciennete = self.compute_anciennete(contract.date_start)
               id = contract.write({'taux_anciennete': anciennete})

class customHREmployee(models.Model):
     _inherit='hr.employee'

     dn_cps = fields.Char('DN (CPS)')

     @api.model
     def year_for_sum(self,month_begin):
          now = datetime.now()
          if now.month >= month_begin:
               begin = datetime(now.year - 1,month_begin,1,0,0,0)
               end = datetime(now.year,month_begin,1,0,0,0) - timedelta(days=1)
          else:
               begin = datetime(now.year - 2,month_begin,1,0,0,0)
               end = datetime(now.year - 1,month_begin,1,0,0,0) - timedelta(days=1)
          return begin.strftime("%Y-%m-%d"),end.strftime("%Y-%m-%d") 

     def month_for_sum(self,date_from):
          date = strptime(date_from, "%Y-%m-%d")
          begin = date - timedelta(days=1)
          begin = datetime(begin.year, begin.month, 1,0,0,0)
          end = date - timedelta(days=1)
          return begin.strftime("%Y-%m-%d"),end.strftime("%Y-%m-%d")

class customHRHolidays(models.Model):
     _inherit='hr.holidays'

     def add_month_holiday(self):
          holy = self
          contract_lines = self.env['hr.contract'].search([('state', '!=', 'close')])
          holyday_type = 1
          description = 'Attribution automatique du ' + fields.Date.today()
          for contract_line in contract_lines:
               emp_id = contract_line.employee_id.id
               conge = contract_line.conge_mensuel
               id = holy.create({'name': description, 'employee_id': emp_id, 'number_of_days_temp': conge, 'state': 'validate', 'holiday_status_id': holyday_type, 'type': 'add'});

class customHRHolidaysStatus(models.Model):
     _inherit='hr.holidays.status'

     code = fields.Char('Code')

class customHRSalaryRule(models.Model):
     _inherit='hr.salary.rule'

     amount_python_base = fields.Text(string='Python Code for Base')

     @api.multi
     def compute_rule(self, localdict):
        """
        :param localdict: dictionary containing the environement in which to compute the rule
        :return: returns a tuple build as the base/amount computed, the quantity and the rate
        :rtype: (float, float, float)
        """
        self.ensure_one()
        if self.amount_select == 'fix':
            try:
                return self.amount_fix, float(safe_eval(self.quantity, localdict)), 100.0
            except:
                raise UserError(_('Wrong quantity defined for salary rule %s (%s).') % (self.name, self.code))
        elif self.amount_select == 'percentage':
            try:
                return (float(safe_eval(self.amount_percentage_base, localdict)),
                        float(safe_eval(self.quantity, localdict)),
                        self.amount_percentage)
            except:
                raise UserError(_('Wrong percentage base or quantity defined for salary rule %s (%s).') % (self.name, self.code))
        else:
            try:
                safe_eval(self.amount_python_compute, localdict, mode='exec', nocopy=True)
		amount = localdict['result']
		result_qty = 'result_qty' in localdict and localdict['result_qty'] or 1.0
                result_rate = 'result_rate' in localdict and localdict['result_rate'] or 100.0
                if self.amount_python_base:
                    safe_eval(self.amount_python_base, localdict, mode="exec", nocopy=True)
                    result_qty = localdict['result']
                return float(amount), float(result_qty), float(result_rate)
            except:
                raise UserError(_('Wrong python code defined for salary rule %s (%s).') % (self.name, self.code))

class customHrPayslip(models.Model):
     _inherit = 'hr.payslip'

     payment_mode = fields.Char(string='Mode de paiement')


     acompte = fields.Float('Acomptes du mois', default = 0)
     heure_comp = fields.Float('Heures complémentaires', default = 0)
     heure_sup_125 = fields.Float('Heures supp. 125%', default = 0)
     heure_sup_150 = fields.Float('Heures supp. 150%', default = 0)
     heure_sup_165 = fields.Float('Heures supp. 165%', default = 0)
     heure_sup_175 = fields.Float('Heures supp. 175%', default = 0)
     heure_sup_200 = fields.Float('Heures supp. 200%', default = 0)

     def get_conge_value(self):
         contract_lines = self.env['hr.contract'].search([('state', '!=', 'close')], limit=1)
         for contract in contract_lines:
             conge = contract.conge_mensuel
         return conge

     conge_acquis = fields.Float('Congé acquis', default = get_conge_value)


     @api.model
     def get_worked_day_lines(self, contract_ids, date_from, date_to):
        """
        @param contract_ids: list of contract id
        @return: returns a list of dict containing the input that should be applied for the given contract between date_from and date_to
        """

        def was_on_leave_interval(employee_id, date_from, date_to):
            date_from = fields.Datetime.to_string(date_from)
            date_to = fields.Datetime.to_string(date_to)
            return self.env['hr.holidays'].search([
                ('state', '=', 'validate'),
                ('employee_id', '=', employee_id),
                ('type', '=', 'remove'),
                ('date_from', '<=', date_from),
                ('date_to', '>=', date_to)
            ], limit=1)

        res = []
        #fill only if the contract as a working schedule linked
        uom_day = self.env.ref('product.product_uom_day', raise_if_not_found=False)
        for contract in self.env['hr.contract'].browse(contract_ids).filtered(lambda contract: contract.working_hours):
            uom_hour = contract.employee_id.resource_id.calendar_id.uom_id or self.env.ref('product.product_uom_hour', raise_if_not_found=False)
            interval_data = []
            holidays = self.env['hr.holidays']
            attendances = {
                 'name': _("Normal Working Days paid at 100%"),
                 'sequence': 1,
                 'code': 'WORK100',
                 'number_of_days': 0.0,
                 'number_of_hours': 0.0,
                 'contract_id': contract.id,
            }
            leaves = {}
            day_from = fields.Datetime.from_string(date_from)
            day_to = fields.Datetime.from_string(date_to)
            nb_of_days = (day_to - day_from).days + 1

            # Gather all intervals and holidays
            for day in range(0, nb_of_days):
                working_intervals_on_day = contract.working_hours.get_working_intervals_of_day(start_dt=day_from + timedelta(days=day))
                for interval in working_intervals_on_day:
                    interval_data.append((interval, was_on_leave_interval(contract.employee_id.id, interval[0], interval[1])))

            # Extract information from previous data. A working interval is considered:
            # - as a leave if a hr.holiday completely covers the period
            # - as a working period instead
            for interval, holiday in interval_data:
                holidays |= holiday
                hours = (interval[1] - interval[0]).total_seconds() / 3600.0
                if holiday:
                    #if he was on leave, fill the leaves dict
                    if holiday.holiday_status_id.name in leaves:
                        leaves[holiday.holiday_status_id.name]['number_of_hours'] += hours
                    else:
                        leaves[holiday.holiday_status_id.name] = {
                            'name': holiday.holiday_status_id.name,
                            'sequence': 5,
                            'code': holiday.holiday_status_id.code,
                            'number_of_days': 0.0,
                            'number_of_hours': hours,
                            'contract_id': contract.id,
                        }
                else:
                    #add the input vals to tmp (increment if existing)
                    attendances['number_of_hours'] += hours

            # Clean-up the results
            leaves = [value for key, value in leaves.items()]
            for data in [attendances] + leaves:
                data['number_of_days'] = uom_hour._compute_quantity(data['number_of_hours'], uom_day)\
                    if uom_day and uom_hour\
                    else data['number_of_hours'] / 8.0
                res.append(data)
        return res

class customHrPayslipLine(models.Model):
    _inherit = 'hr.payslip.line'

    total = fields.Float(compute='_compute_total', string='Total', digits=dp.get_precision('Payroll PF'), store=True)

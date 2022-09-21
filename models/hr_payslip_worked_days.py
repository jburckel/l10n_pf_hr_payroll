from odoo import api, fields, models


class HrPayslipWorkedDays(models.Model):
    _inherit = "hr.payslip.worked_days"

    @api.model
    def create(self, values):
        if not values.get('contract_id'):
            payslip = self.env['hr.payslip'].search(
                [('id', '=', values['payslip_id'])],
                limit=1
            )
            if payslip:
                values['contract_id'] = payslip[0].contract_id.id

        if not values.get('name'):
            values['name'] = values.get('code').title()

        return super(HrPayslipWorkedDays, self).create(values)

    def write(self, values):
        if 'contract_id' in values and not values.get('contract_id', False) :
            payslip_id = values.get('payslip_id', False) or self.payslip_id.id
            payslip = self.env['hr.payslip'].search(
                [('id', '=', payslip_id)],
                limit=1
            )
            if payslip:
                values['contract_id'] = payslip[0].contract_id.id
        if 'name' in values and not values.get('name', None):
            code = values.get('code', False) or self.code
            values['name'] = code.title()

        return super(HrPayslipWorkedDays, self).write(values)
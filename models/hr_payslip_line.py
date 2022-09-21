from odoo import api, models


class HrPayslipLine(models.Model):
    _inherit = 'hr.payslip.line'

    @api.depends("quantity", "amount", "rate")
    def _compute_total(self):
        for line in self:
            line.total = round(float(line.quantity) * line.amount * line.rate / 100)
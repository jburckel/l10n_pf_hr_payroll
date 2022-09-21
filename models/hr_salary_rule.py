from odoo import fields, models, _
from odoo.exceptions import UserError
from odoo.tools.safe_eval import safe_eval

class HRSalaryRule(models.Model):
    _inherit = 'hr.salary.rule'

    amount_python_base = fields.Text(string='Python Code for Base')

    def _compute_rule(self, localdict):
        """
        :param localdict: dictionary containing the environement in which to
                          compute the rule
        :return: returns a tuple build as the base/amount computed, the quantity
                 and the rate
        :rtype: (float, float, float)
        """
        amount, qty, rate, name = super(HRSalaryRule, self)._compute_rule(localdict)

        if self.amount_select == "code" and self.amount_python_base:
            try:
                safe_eval(
                    self.amount_python_base, localdict, mode="exec", nocopy=True
                )
                qty = float(localdict["result"])
            except Exception as ex:
                raise UserError(
                    _(
                        """
Wrong python code defined for python code for base %s (%s).
Here is the error received:
%s
"""
                    )
                    % (self.name, self.code, repr(ex))
                )
        return (
            amount,
            qty,
            rate,
            name
        )
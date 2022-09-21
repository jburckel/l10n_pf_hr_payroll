from datetime import datetime, timedelta
from time import strptime

from odoo import api, fields, models

class HREmployee(models.Model):
    _inherit = 'hr.employee'

    dn_cps = fields.Char('DN (CPS)')

    @api.model
    def year_for_sum(self, month_begin):
        now = datetime.now()
        if now.month >= month_begin:
            begin = datetime(now.year - 1, month_begin, 1, 0, 0, 0)
            end = datetime(now.year, month_begin, 1, 0, 0, 0) - timedelta(days=1)
        else:
            begin = datetime(now.year - 2, month_begin, 1, 0, 0, 0)
            end = datetime(now.year - 1, month_begin, 1, 0, 0, 0) - timedelta(days=1)
        return begin.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")

    def month_for_sum(self, date_from):
        date = strptime(date_from, "%Y-%m-%d")
        begin = date - timedelta(days=1)
        begin = datetime(begin.year, begin.month, 1, 0, 0, 0)
        end = date - timedelta(days=1)
        return begin.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")



from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    add_leave_attribution_when_done = fields.Boolean(
        string="Ajouter une attribution de congés à la validation du bulletin",
        config_parameter='l10n_pf_hr_payroll.add_leave_attribution_when_done'

    )
    validate_leave_when_done = fields.Boolean(
        string="Valider les congés enregistrés à la validation du bulletin",
        config_parameter='l10n_pf_hr_payroll.validate_leave_when_done'
    )

    holiday_code = fields.Many2one(
        "hr.leave.type",
        string="Code pour les congés",
        config_parameter="l10n_pf_hr_payroll.holiday_code"
    )
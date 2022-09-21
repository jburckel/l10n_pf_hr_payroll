from datetime import date
from math import floor

from odoo import api, fields, models


class HRContract(models.Model):
    _inherit = 'hr.contract'

    heure_mensuelle = fields.Integer('Horaire mensuel', default=169)
    taux_horaire = fields.Float('Taux horaire')
    conge_mensuel = fields.Float(string='Congés mensuels attribués', default=2.5)
    indemnite_conge_paye = fields.Float('Indemnité de congé payé (par jour)')
    taux_anciennete = fields.Float('Anciennete')
    jours_travailles = fields.Float('Nombre de jours travaillés', default=5)

    @api.onchange('wage', 'heure_mensuelle')
    def update_field(self):
        if self.heure_mensuelle > 0:
            self.taux_horaire = self.wage / self.heure_mensuelle

    def compute_anciennete(self, date_start):
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
            contract.write({'taux_anciennete': anciennete})



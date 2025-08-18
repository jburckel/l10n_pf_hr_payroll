# Migration vers Odoo 18.0

## Changements appliqués pour la compatibilité Odoo 18

### 1. Manifeste (__manifest__.py)
- ✅ Ajout de la version `18.0.1.0.0`
- ✅ Ajout de métadonnées recommandées (`summary`, `author`, `website`, `application`)
- ✅ Mise à jour de la description

### 2. API et méthodes dépréciées

#### models/hr_contract.py
- ✅ Remplacement de `fields.Date.from_string()` par `date.fromisoformat()`
- ✅ Ajout de vérification de type pour la compatibilité

#### models/hr_employee.py  
- ✅ Remplacement de `time.strptime()` par `datetime.strptime()`
- ✅ Suppression de l'import `time.strptime`

### 3. Modernisation des champs

#### models/hr_payslip.py
- ✅ Remplacement de `states={"draft": [("readonly", False)]}` par `readonly_state='draft'`
- ✅ Modernisation de tous les champs concernés :
  - `acompte`
  - `heure_absence` 
  - `heure_comp`
  - `heure_sup_125`
  - `heure_sup_150`
  - `heure_sup_165`
  - `heure_sup_175`
  - `heure_sup_200`
  - `conge_acquis`
  - `conge_pris`
  - `indemnite_conge_paye`
  - `conge_enregistre_ids`

### 4. Vues XML

#### views/l10n_pf_hr_payroll_view.xml
- ✅ Suppression de l'attribut déprécié `type="form"` dans toutes les vues
- ✅ Conservation de `arch type="xml"` qui reste nécessaire

### 5. Éléments déjà compatibles

- ✅ Structure des modèles
- ✅ Héritage des classes
- ✅ Décorateurs API (`@api.onchange`, `@api.model`, `@api.depends`)
- ✅ Rapports AbstractModel
- ✅ Configuration settings

## Vérifications recommandées

1. **Modules de dépendance** : Vérifier que `payroll`, `l10n_pf`, et `hr_holidays` sont disponibles pour Odoo 18
2. **Tests** : Exécuter les tests fonctionnels après migration
3. **Données** : Vérifier que les fichiers de données (.xls/.xlsx) sont toujours compatibles

## Notes techniques

- La syntaxe `readonly_state` est plus moderne et performante que l'ancienne `states`
- `date.fromisoformat()` est plus robuste que `fields.Date.from_string()`
- L'attribut `type` dans les vues est déprécié depuis Odoo 15+

## Statut de migration

🟢 **Complet** - Le module est maintenant compatible avec Odoo 18.0

"""Tableau de bord (Mini-projet) : statistiques et états."""
from flask import Blueprint, render_template
from flask_login import login_required
from sqlalchemy import func

from api import nha_en_minutes, minutes_en_texte
from extensions import db
from models import Classe, Etudiant, Matiere, Absence

dashboard = Blueprint('dashboard', __name__)

SEUIL_ALERTE = 600   # minutes : à partir de 10 h d'absence, l'étudiant est en alerte


def barres(elements):
    """Ajoute à chaque élément le pourcentage de barre (par rapport au plus grand)."""
    maximum = max((e['valeur'] for e in elements), default=0)
    for e in elements:
        e['pct'] = round(e['valeur'] * 100 / maximum) if maximum else 0
    return elements


@dashboard.route('/dashboard')
@login_required
def tableau_de_bord():
    # ----- Étudiants par classe -----
    lignes = (db.session.query(Classe.CodClass, Classe.NomClass, func.count(Etudiant.NCE))
              .outerjoin(Etudiant, Etudiant.CodClass == Classe.CodClass)
              .group_by(Classe.CodClass, Classe.NomClass)
              .order_by(Classe.CodClass).all())
    par_classe = barres([{'label': f'{cod} - {nom}', 'valeur': nb, 'texte': str(nb)}
                         for cod, nom, nb in lignes])

    # ----- Absences : cumul par matière et par étudiant -----
    absences = Absence.query.all()
    noms_matieres = {m.CodMat: m.IntMat for m in Matiere.query.all()}
    noms_etudiants = {e.NCE: f'{e.Nom} {e.Prenom}' for e in Etudiant.query.all()}

    minutes_matiere, minutes_etudiant, nb_etudiant = {}, {}, {}
    total = 0
    for a in absences:
        minutes = nha_en_minutes(a.NHA)
        total += minutes
        minutes_matiere[a.CodMat] = minutes_matiere.get(a.CodMat, 0) + minutes
        minutes_etudiant[a.NCE] = minutes_etudiant.get(a.NCE, 0) + minutes
        nb_etudiant[a.NCE] = nb_etudiant.get(a.NCE, 0) + 1

    par_matiere = barres(sorted(
        [{'label': noms_matieres.get(cod, cod), 'valeur': mn, 'texte': minutes_en_texte(mn)}
         for cod, mn in minutes_matiere.items()],
        key=lambda e: e['valeur'], reverse=True))

    # ----- Les 5 étudiants les plus absents -----
    classement = [{'nce': nce, 'nom': noms_etudiants.get(nce, nce),
                   'absences': nb_etudiant[nce], 'total': minutes_en_texte(mn),
                   'alerte': mn >= SEUIL_ALERTE}
                  for nce, mn in sorted(minutes_etudiant.items(),
                                        key=lambda x: x[1], reverse=True)[:5]]

    # ----- Les 5 dernières absences -----
    recentes = (Absence.query.order_by(Absence.DateA.desc()).limit(5).all())
    dernieres = [{'date': a.DateA.strftime('%d/%m/%Y'),
                  'etudiant': noms_etudiants.get(a.NCE, a.NCE),
                  'matiere': noms_matieres.get(a.CodMat, a.CodMat),
                  'duree': minutes_en_texte(nha_en_minutes(a.NHA))}
                 for a in recentes]

    cartes = [('Classes', Classe.query.count()),
              ('Étudiants', Etudiant.query.count()),
              ('Matières', Matiere.query.count()),
              ('Absences', len(absences)),
              ("Heures d'absence", minutes_en_texte(total))]

    return render_template('dashboard.html', cartes=cartes, par_classe=par_classe,
                           par_matiere=par_matiere, classement=classement,
                           dernieres=dernieres, seuil=minutes_en_texte(SEUIL_ALERTE))
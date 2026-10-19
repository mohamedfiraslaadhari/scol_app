"""API REST (Mini-projet) : accès JSON aux données de la base."""
from flask import Blueprint, jsonify, url_for
from flask_login import current_user
from sqlalchemy import func

from extensions import db
from models import User, Classe, Etudiant, Matiere, Absence

api = Blueprint('api', __name__, url_prefix='/api')


@api.before_request
def exiger_connexion():
    """Toute l'API demande d'être connecté (réponse JSON, pas de redirection)."""
    if not current_user.is_authenticated:
        return jsonify(erreur='Authentification requise'), 401


# ---------- Conversion des objets en dictionnaires JSON ----------
def nha_en_minutes(nha):
    """1.45 (= 1h45) -> 105 minutes."""
    heures = int(nha)
    return heures * 60 + round((nha - heures) * 100)


def minutes_en_texte(minutes):
    return f'{minutes // 60}h{minutes % 60:02d}'


def classe_json(c):
    return {'code': c.CodClass, 'nom': c.NomClass, 'nombre_etudiants': c.NbrEtud}


def etudiant_json(e):
    photo = None
    if e.photo:
        photo = url_for('static', filename='image/' + e.photo, _external=True)
    return {'nce': e.NCE, 'nom': e.Nom, 'prenom': e.Prenom,
            'date_naissance': e.DateNais.isoformat() if e.DateNais else None,
            'lieu_naissance': e.LieuNais, 'classe': e.CodClass, 'photo': photo}


def matiere_json(m):
    return {'code': m.CodMat, 'intitule': m.IntMat, 'description': m.Description}


def absence_json(a):
    return {'nce': a.NCE, 'matiere': a.CodMat, 'date': a.DateA.isoformat(),
            'heures': a.NHA, 'duree': minutes_en_texte(nha_en_minutes(a.NHA))}


def introuvable(nom):
    return jsonify(erreur=f'{nom} introuvable'), 404


# ---------- Classes ----------
@api.route('/classes')
def liste_classes():
    classes = Classe.query.order_by(Classe.CodClass).all()
    return jsonify([classe_json(c) for c in classes])


@api.route('/classes/<code>')
def detail_classe(code):
    classe = db.session.get(Classe, code)
    if classe is None:
        return introuvable('Classe')
    donnees = classe_json(classe)
    donnees['etudiants'] = [etudiant_json(e) for e in classe.etudiants]
    return jsonify(donnees)


# ---------- Étudiants ----------
@api.route('/etudiants')
def liste_etudiants():
    etudiants = Etudiant.query.order_by(Etudiant.Nom).all()
    return jsonify([etudiant_json(e) for e in etudiants])


@api.route('/etudiants/<nce>')
def detail_etudiant(nce):
    etudiant = db.session.get(Etudiant, nce)
    if etudiant is None:
        return introuvable('Étudiant')
    return jsonify(etudiant_json(etudiant))


@api.route('/etudiants/<nce>/absences')
def absences_etudiant_api(nce):
    etudiant = db.session.get(Etudiant, nce)
    if etudiant is None:
        return introuvable('Étudiant')
    absences = Absence.query.filter_by(NCE=nce).order_by(Absence.DateA).all()
    total = sum(nha_en_minutes(a.NHA) for a in absences)
    return jsonify({'etudiant': etudiant_json(etudiant),
                    'total': minutes_en_texte(total),
                    'absences': [absence_json(a) for a in absences]})


# ---------- Matières ----------
@api.route('/matieres')
def liste_matieres_api():
    matieres = Matiere.query.order_by(Matiere.CodMat).all()
    return jsonify([matiere_json(m) for m in matieres])


# ---------- Absences ----------
@api.route('/absences')
def liste_absences():
    absences = Absence.query.order_by(Absence.DateA.desc()).all()
    return jsonify([absence_json(a) for a in absences])


# ---------- Statistiques ----------
@api.route('/stats')
def statistiques():
    absences = Absence.query.all()
    total = sum(nha_en_minutes(a.NHA) for a in absences)
    return jsonify({
        'classes': Classe.query.count(),
        'etudiants': Etudiant.query.count(),
        'matieres': Matiere.query.count(),
        'absences': len(absences),
        'total_heures_absence': minutes_en_texte(total),
    })


# ---------- Utilisateurs (administrateur uniquement) ----------
@api.route('/users')
def liste_users():
    if not current_user.is_admin():
        return jsonify(erreur='Accès réservé aux administrateurs'), 403
    users = User.query.order_by(User.id).all()
    # Le mot de passe n'est jamais renvoyé
    return jsonify([{'id': u.id, 'username': u.username, 'email': u.email,
                     'role': u.role} for u in users])
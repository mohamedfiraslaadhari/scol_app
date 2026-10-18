"""Interface d'administration Flask-Admin (TD2), réservée aux administrateurs (TP)."""
from flask import flash, redirect, request, url_for
from flask_admin import Admin, AdminIndexView
from flask_admin.contrib.sqla import ModelView
from flask_admin.menu import MenuLink
from flask_babel import Babel
from flask_login import current_user
from passlib.hash import pbkdf2_sha256
from wtforms import FloatField, PasswordField, ValidationError
from wtforms.validators import DataRequired, Email, InputRequired, Length

from extensions import db
from models import User, Classe, Etudiant, Matiere, Absence


class AdminAccessMixin:
    """Seuls les utilisateurs connectés avec le rôle 'admin' peuvent entrer."""

    def is_accessible(self):
        return current_user.is_authenticated and current_user.is_admin()

    def inaccessible_callback(self, name, **kwargs):
        if current_user.is_authenticated:
            flash('Accès réservé aux administrateurs.', 'danger')
            return redirect(url_for('index'))
        return redirect(url_for('login', next=request.path))


class SecureIndexView(AdminAccessMixin, AdminIndexView):
    """Page d'accueil de l'administration (protégée)."""


def maj_effectifs():
    """Recalcule NbrEtud (nombre d'étudiants) de toutes les classes."""
    for classe in Classe.query.all():
        classe.NbrEtud = Etudiant.query.filter_by(CodClass=classe.CodClass).count()
    db.session.commit()


class UserAdmin(AdminAccessMixin, ModelView):
    """Vue d'administration du modèle User (avec gestion des rôles)."""
    page_size = 5
    can_set_page_size = True
    page_size_options = (5, 10, 20, 50)

    column_list = ['id', 'username', 'email', 'role']   # le mot de passe n'est jamais affiché
    # 'new_password' doit être listé ici, sinon le champ n'apparaît pas
    form_columns = ['username', 'email', 'role', 'new_password']
    form_choices = {'role': [('user', 'Utilisateur'), ('admin', 'Administrateur')]}
    # Champ virtuel (pas une colonne de la base) : il ne contient jamais le hash existant
    form_extra_fields = {'new_password': PasswordField('Password')}

    form_args = {
        'username': {'validators': [DataRequired(), Length(min=4, max=20)]},
        'email': {'validators': [DataRequired(), Email()]},
    }

    def on_model_change(self, form, model, is_created):
        """Hache le mot de passe avant l'enregistrement."""
        pwd = form.new_password.data
        if pwd:
            if len(pwd) < 6:
                raise ValidationError('Le mot de passe doit avoir au moins 6 caractères.')
            model.password = pbkdf2_sha256.hash(pwd)
        elif is_created:
            raise ValidationError('Le mot de passe est obligatoire.')
        # En modification, un champ vide garde l'ancien mot de passe


class ClasseAdmin(AdminAccessMixin, ModelView):
    """Classes : NbrEtud est calculé automatiquement."""
    column_list = ['CodClass', 'NomClass', 'NbrEtud']
    form_columns = ['CodClass', 'NomClass']
    column_searchable_list = ['CodClass', 'NomClass']
    can_set_page_size = True
    page_size_options = (10, 20, 50)
    column_labels = {
        'CodClass': 'Code classe', 'NomClass': 'Nom de la classe',
        'NbrEtud': "Nombre d'étudiants",
    }


class EtudiantAdmin(AdminAccessMixin, ModelView):
    """Étudiants : la classe est choisie dans une liste déroulante."""
    column_list = ['NCE', 'Nom', 'Prenom', 'DateNais', 'LieuNais', 'classe']
    form_columns = ['NCE', 'Nom', 'Prenom', 'DateNais', 'LieuNais', 'classe']
    column_searchable_list = ['NCE', 'Nom', 'Prenom']
    column_filters = ['classe.CodClass']
    can_set_page_size = True
    page_size_options = (10, 20, 50)
    column_labels = {
        'NCE': 'NCE', 'Nom': 'Nom', 'Prenom': 'Prénom',
        'DateNais': 'Date de naissance', 'LieuNais': 'Lieu de naissance',
        'classe': 'Classe',
    }

    def after_model_change(self, form, model, is_created):
        maj_effectifs()

    def after_model_delete(self, model):
        maj_effectifs()


class MatiereAdmin(AdminAccessMixin, ModelView):
    column_list = ['CodMat', 'IntMat', 'Description']
    form_columns = ['CodMat', 'IntMat', 'Description']
    column_searchable_list = ['CodMat', 'IntMat']
    can_set_page_size = True
    page_size_options = (10, 20, 50)
    column_labels = {
        'CodMat': 'Code matière', 'IntMat': 'Intitulé', 'Description': 'Description',
    }


class AbsenceAdmin(AdminAccessMixin, ModelView):
    """Absences : l'étudiant et la matière sont choisis dans des listes."""
    column_list = ['etudiant', 'matiere', 'DateA', 'NHA']
    # NHA est déclaré explicitement ci-dessous (form_extra_fields)
    form_columns = ['etudiant', 'matiere', 'DateA', 'NHA']
    form_extra_fields = {
        'NHA': FloatField("Nombre d'heures (1.45 = 1h45)", validators=[InputRequired()]),
    }
    column_filters = ['DateA', 'matiere.CodMat']
    can_set_page_size = True
    page_size_options = (10, 20, 50)
    column_labels = {
        'etudiant': 'Étudiant', 'matiere': 'Matière',
        'DateA': "Date d'absence", 'NHA': "Nombre d'heures",
    }


def init_admin(app, csrf):
    """Initialise Babel et Flask-Admin sur l'application."""
    Babel(app)  # extension de traduction demandée par le TD

    admin = Admin(app, name='Scolarité', index_view=SecureIndexView(name='Admin Panel'))
    admin.add_view(UserAdmin(User, db.session))
    admin.add_view(ClasseAdmin(Classe, db.session))
    admin.add_view(EtudiantAdmin(Etudiant, db.session))
    admin.add_view(MatiereAdmin(Matiere, db.session))
    admin.add_view(AbsenceAdmin(Absence, db.session))

    # Liens de navigation dans le menu de l'administration
    admin.add_link(MenuLink(name="Retour à l'application", url='/'))
    admin.add_link(MenuLink(name='Déconnexion', url='/logout'))

    # Flask-Admin gère ses propres formulaires : on les exclut du CSRFProtect global
    for view in admin._views:
        if getattr(view, 'blueprint', None) is not None:
            csrf.exempt(view.blueprint)
    return admin
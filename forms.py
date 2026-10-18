from flask_wtf import FlaskForm
from wtforms import (StringField, PasswordField, SelectField, DateField,
                     FloatField, TextAreaField, SubmitField)
from wtforms.validators import (DataRequired, Email, Length, EqualTo,
                                NumberRange, Optional, ValidationError)

from models import User, Classe, Etudiant, Matiere


class UserForm(FlaskForm):
    username = StringField("Nom d'utilisateur", validators=[
        DataRequired(message='Champ obligatoire'),
        Length(min=3, max=80, message='Entre 3 et 80 caractères')])
    email = StringField('Email', validators=[
        DataRequired(message='Champ obligatoire'),
        Email(message='Email invalide')])
    password = PasswordField('Mot de passe', validators=[
        DataRequired(message='Champ obligatoire'),
        Length(min=6, message='Minimum 6 caractères')])
    confirm = PasswordField('Confirmer le mot de passe', validators=[
        DataRequired(message='Champ obligatoire'),
        EqualTo('password', message='Les mots de passe ne correspondent pas')])
    submit = SubmitField('Ajouter')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('Cet email existe déjà')


class ClasseForm(FlaskForm):
    CodClass = StringField('Code classe (ex : IngTA2-D)', validators=[
        DataRequired(message='Champ obligatoire'),
        Length(max=20, message='Maximum 20 caractères')])
    NomClass = StringField('Nom de la classe', validators=[
        DataRequired(message='Champ obligatoire'),
        Length(max=50, message='Maximum 50 caractères')])
    submit = SubmitField('Ajouter la classe')

    def validate_CodClass(self, field):
        if db_exists(Classe, field.data.strip()):
            raise ValidationError('Ce code de classe existe déjà')


class EtudiantForm(FlaskForm):
    NCE = StringField('NCE (numéro carte étudiant)', validators=[
        DataRequired(message='Champ obligatoire'),
        Length(max=20, message='Maximum 20 caractères')])
    Nom = StringField('Nom', validators=[
        DataRequired(message='Champ obligatoire'),
        Length(max=50, message='Maximum 50 caractères')])
    Prenom = StringField('Prénom', validators=[
        DataRequired(message='Champ obligatoire'),
        Length(max=50, message='Maximum 50 caractères')])
    DateNais = DateField('Date de naissance (optionnel)', validators=[Optional()])
    LieuNais = StringField('Lieu de naissance (optionnel)', validators=[
        Optional(), Length(max=50, message='Maximum 50 caractères')])
    CodClass = SelectField('Classe', validators=[DataRequired(message='Choisissez une classe')])
    submit = SubmitField("Ajouter l'étudiant")

    def validate_NCE(self, field):
        if db_exists(Etudiant, field.data.strip()):
            raise ValidationError('Ce NCE existe déjà')


class MatiereForm(FlaskForm):
    CodMat = StringField('Code matière (ex : ProgWebPyt)', validators=[
        DataRequired(message='Champ obligatoire'),
        Length(max=20, message='Maximum 20 caractères')])
    IntMat = StringField('Intitulé', validators=[
        DataRequired(message='Champ obligatoire'),
        Length(max=100, message='Maximum 100 caractères')])
    Description = TextAreaField('Description (optionnel)', validators=[Optional()])
    submit = SubmitField('Ajouter la matière')

    def validate_CodMat(self, field):
        if db_exists(Matiere, field.data.strip()):
            raise ValidationError('Ce code de matière existe déjà')


class AbsenceForm(FlaskForm):
    NCE = SelectField('Étudiant', validators=[DataRequired()])
    CodMat = SelectField('Matière', validators=[DataRequired()])
    DateA = DateField("Date d'absence", validators=[DataRequired(message='Date invalide')])
    NHA = FloatField("Nombre d'heures (1.45 = 1h45)", validators=[
        DataRequired(message='Champ obligatoire'),
        NumberRange(min=0.15, max=8, message='Valeur entre 0.15 et 8')])
    submit = SubmitField('Enregistrer')


def db_exists(model, pk):
    """Vrai si une ligne avec cette clé primaire existe déjà."""
    from extensions import db
    return db.session.get(model, pk) is not None
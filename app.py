import os
from datetime import date
from functools import wraps
from urllib.parse import urlparse

from flask import (Flask, render_template, redirect, url_for, flash, abort,
                   request)
from flask_login import (LoginManager, login_user, logout_user, login_required,
                         current_user)
from flask_uploads import UploadSet, configure_uploads, UploadNotAllowed
from flask_wtf.csrf import CSRFProtect
from passlib.hash import pbkdf2_sha256
from sqlalchemy.exc import IntegrityError
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename

from config import Config
from extensions import db, migrate
from models import User, Classe, Etudiant, Matiere, Absence
from forms import (UserForm, ClasseForm, EtudiantForm, EtudiantEditForm,
                   MatiereForm, AbsenceForm, LoginForm, EXTENSIONS_IMAGES)
from admin_views import init_admin

app = Flask(__name__)
app.config.from_object(Config)

# ---------- Téléchargement des photos (TD3 : Flask-Uploads) ----------
app.config['UPLOADED_PHOTOS_DEST'] = os.path.join(app.root_path, 'static', 'image')
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024   # taille maximale : 2 Mo
os.makedirs(app.config['UPLOADED_PHOTOS_DEST'], exist_ok=True)
photos = UploadSet('photos', tuple(EXTENSIONS_IMAGES))  # "photos" = nom de l'ensemble d'uploads
configure_uploads(app, photos)

db.init_app(app)
migrate.init_app(app, db)
csrf = CSRFProtect(app)  # protège aussi les boutons "Supprimer" (POST)

# ---------- Sessions utilisateurs (TP : Flask-Login) ----------
login_manager = LoginManager(app)
login_manager.login_view = 'login'            # page vers laquelle on redirige si non connecté
login_manager.login_message = 'Veuillez vous connecter pour accéder à cette page.'
login_manager.login_message_category = 'danger'


@login_manager.user_loader
def load_user(user_id):
    """Recharge l'utilisateur à partir de l'identifiant stocké dans la session."""
    return db.session.get(User, int(user_id))


def admin_required(vue):
    """Réserve une route aux administrateurs (rôle 'admin')."""
    @wraps(vue)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated:
            return login_manager.unauthorized()
        if not current_user.is_admin():
            flash('Accès réservé aux administrateurs.', 'danger')
            return redirect(url_for('index'))
        return vue(*args, **kwargs)
    return wrapper


def adresse_sure(cible):
    """Accepte uniquement une adresse interne (évite la redirection vers un autre site)."""
    if not cible:
        return False
    analyse = urlparse(cible)
    return (cible.startswith('/') and not cible.startswith('//')
            and '\\' not in cible and not analyse.netloc and not analyse.scheme)


init_admin(app, csrf)  # interface /admin (Flask-Admin), réservée aux administrateurs
app.app_context().push()  # contexte d'application hors requête HTTP (TD, Partie 1 - point 2)


def maj_effectif(cod_class):
    """Recalcule NbrEtud (nombre d'étudiants) d'une classe."""
    classe = db.session.get(Classe, cod_class)
    if classe:
        classe.NbrEtud = Etudiant.query.filter_by(CodClass=cod_class).count()
        db.session.commit()


def sauver_photo(fichier, nce):
    """Enregistre l'image sous le nom <NCE>.<extension> et retourne le nom du fichier."""
    base = secure_filename(nce) or 'etudiant'
    return photos.save(fichier, name=f'{base}.')


def supprimer_photo(nom_fichier):
    """Supprime le fichier image du disque (s'il existe)."""
    if nom_fichier:
        chemin = os.path.join(app.config['UPLOADED_PHOTOS_DEST'], os.path.basename(nom_fichier))
        if os.path.isfile(chemin):
            os.remove(chemin)


def fichier_envoye(champ):
    """Vrai si l'utilisateur a réellement choisi un fichier dans le champ photo."""
    return isinstance(champ.data, FileStorage) and bool(champ.data.filename)


# ================= CONNEXION / DÉCONNEXION =================
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data.strip()).first()
        try:
            mot_de_passe_ok = bool(user) and pbkdf2_sha256.verify(form.password.data, user.password)
        except ValueError:          # mot de passe stocké dans un format inconnu
            mot_de_passe_ok = False
        if mot_de_passe_ok:
            login_user(user)        # Flask-Login mémorise l'utilisateur dans la session
            flash(f'Bienvenue {user.username} ! Vous êtes connecté.', 'success')
            cible = request.args.get('next')
            return redirect(cible if adresse_sure(cible) else url_for('index'))
        flash('Identifiants incorrects.', 'danger')
    return render_template('login.html', form=form)


@app.route('/logout', methods=['GET', 'POST'])   # GET autorisé pour le lien du menu /admin
@login_required
def logout():
    logout_user()                   # supprime l'utilisateur de la session
    flash('Vous avez été déconnecté.', 'success')
    return redirect(url_for('login'))


# ================= ÉTUDIANTS (page d'accueil) =================
@app.route('/')
@login_required
def index():
    etudiants = Etudiant.query.order_by(Etudiant.Nom).all()
    return render_template('index.html', etudiants=etudiants)


@app.route('/etudiant/add', methods=['GET', 'POST'])
@admin_required
def add_etudiant():
    classes = Classe.query.order_by(Classe.CodClass).all()
    if not classes:
        flash("Ajoutez d'abord une classe.", 'danger')
        return redirect(url_for('list_classes'))

    form = EtudiantForm()
    form.CodClass.choices = [(c.CodClass, f'{c.CodClass} - {c.NomClass}') for c in classes]

    if form.validate_on_submit():
        nce = form.NCE.data.strip()
        nom_photo = None
        if fichier_envoye(form.photo):
            try:
                nom_photo = sauver_photo(form.photo.data, nce)
            except UploadNotAllowed:
                flash('Type de fichier non autorisé.', 'danger')
                return render_template('add_etudiant.html', form=form)

        db.session.add(Etudiant(NCE=nce,
                                Nom=form.Nom.data.strip(),
                                Prenom=form.Prenom.data.strip(),
                                DateNais=form.DateNais.data,
                                LieuNais=(form.LieuNais.data or '').strip() or None,
                                CodClass=form.CodClass.data,
                                photo=nom_photo))
        db.session.commit()
        maj_effectif(form.CodClass.data)
        flash('Étudiant ajouté.', 'success')
        return redirect(url_for('index'))
    return render_template('add_etudiant.html', form=form)


@app.route('/etudiant/<nce>/edit', methods=['GET', 'POST'])
@admin_required
def edit_etudiant(nce):
    etudiant = db.get_or_404(Etudiant, nce)
    classes = Classe.query.order_by(Classe.CodClass).all()

    form = EtudiantEditForm(obj=etudiant)
    form.CodClass.choices = [(c.CodClass, f'{c.CodClass} - {c.NomClass}') for c in classes]

    if form.validate_on_submit():
        ancienne_classe = etudiant.CodClass
        etudiant.Nom = form.Nom.data.strip()
        etudiant.Prenom = form.Prenom.data.strip()
        etudiant.DateNais = form.DateNais.data
        etudiant.LieuNais = (form.LieuNais.data or '').strip() or None
        etudiant.CodClass = form.CodClass.data

        if fichier_envoye(form.photo):
            try:
                nouvelle = sauver_photo(form.photo.data, nce)
            except UploadNotAllowed:
                db.session.rollback()
                flash('Type de fichier non autorisé.', 'danger')
                return render_template('edit_etudiant.html', form=form, etudiant=etudiant)
            if etudiant.photo and etudiant.photo != nouvelle:
                supprimer_photo(etudiant.photo)   # on retire l'ancienne photo
            etudiant.photo = nouvelle
        # sinon : aucune nouvelle photo, on conserve l'ancienne

        db.session.commit()
        maj_effectif(ancienne_classe)
        maj_effectif(etudiant.CodClass)
        flash("Informations de l'étudiant mises à jour.", 'success')
        return redirect(url_for('index'))
    return render_template('edit_etudiant.html', form=form, etudiant=etudiant)


@app.route('/etudiant/<nce>/delete', methods=['POST'])
@admin_required
def delete_etudiant(nce):
    etudiant = db.get_or_404(Etudiant, nce)
    cod_class = etudiant.CodClass
    nom_photo = etudiant.photo
    try:
        db.session.delete(etudiant)  # ses absences sont supprimées aussi
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        flash("Impossible de supprimer l'étudiant : il est lié à d'autres enregistrements.", 'danger')
        return redirect(url_for('index'))
    supprimer_photo(nom_photo)
    maj_effectif(cod_class)
    flash('Étudiant supprimé (et ses absences).', 'success')
    return redirect(url_for('index'))


# ================= CLASSES (administrateur) =================
@app.route('/classes', methods=['GET', 'POST'])
@admin_required
def list_classes():
    form = ClasseForm()
    if form.validate_on_submit():
        db.session.add(Classe(CodClass=form.CodClass.data.strip(),
                              NomClass=form.NomClass.data.strip(),
                              NbrEtud=0))
        db.session.commit()
        flash('Classe ajoutée.', 'success')
        return redirect(url_for('list_classes'))
    classes = Classe.query.order_by(Classe.CodClass).all()
    return render_template('classes.html', form=form, classes=classes)


@app.route('/classe/<cod>/delete', methods=['POST'])
@admin_required
def delete_classe(cod):
    classe = db.get_or_404(Classe, cod)
    db.session.delete(classe)  # ses étudiants et leurs absences sont supprimés aussi
    db.session.commit()
    flash('Classe supprimée (avec ses étudiants et leurs absences).', 'success')
    return redirect(url_for('list_classes'))


# ================= MATIÈRES (administrateur) =================
@app.route('/matieres', methods=['GET', 'POST'])
@admin_required
def list_matieres():
    form = MatiereForm()
    if form.validate_on_submit():
        db.session.add(Matiere(CodMat=form.CodMat.data.strip(),
                               IntMat=form.IntMat.data.strip(),
                               Description=(form.Description.data or '').strip() or None))
        db.session.commit()
        flash('Matière ajoutée.', 'success')
        return redirect(url_for('list_matieres'))
    matieres = Matiere.query.order_by(Matiere.CodMat).all()
    return render_template('matieres.html', form=form, matieres=matieres)


@app.route('/matiere/<cod>/delete', methods=['POST'])
@admin_required
def delete_matiere(cod):
    matiere = db.get_or_404(Matiere, cod)
    db.session.delete(matiere)  # ses absences sont supprimées aussi
    db.session.commit()
    flash('Matière supprimée (et ses absences).', 'success')
    return redirect(url_for('list_matieres'))


# ================= ABSENCES =================
@app.route('/absences/<nce>')
@login_required
def absences_etudiant(nce):
    etudiant = db.get_or_404(Etudiant, nce)
    absences = (Absence.query.filter_by(NCE=nce)
                .order_by(Absence.DateA).all())
    return render_template('absece_Etudiant.html', etudiant=etudiant, absences=absences)


@app.route('/absence/add', methods=['GET', 'POST'])
@login_required
def add_absence():
    etudiants = Etudiant.query.order_by(Etudiant.Nom).all()
    matieres = Matiere.query.order_by(Matiere.IntMat).all()
    if not etudiants or not matieres:
        flash("Ajoutez d'abord au moins un étudiant et une matière.", 'danger')
        return redirect(url_for('index'))

    form = AbsenceForm()
    form.NCE.choices = [(e.NCE, f'{e.NCE} - {e.Nom} {e.Prenom}') for e in etudiants]
    form.CodMat.choices = [(m.CodMat, f'{m.CodMat} - {m.IntMat}') for m in matieres]

    if form.validate_on_submit():
        if db.session.get(Absence, (form.CodMat.data, form.NCE.data, form.DateA.data)):
            flash('Cette absence existe déjà.', 'danger')
        else:
            db.session.add(Absence(CodMat=form.CodMat.data, NCE=form.NCE.data,
                                   DateA=form.DateA.data, NHA=form.NHA.data))
            db.session.commit()
            flash('Absence enregistrée.', 'success')
            return redirect(url_for('absences_etudiant', nce=form.NCE.data))
    return render_template('add_absence.html', form=form)


@app.route('/absence/delete/<codmat>/<nce>/<jour>', methods=['POST'])
@admin_required
def delete_absence(codmat, nce, jour):
    absence = db.session.get(Absence, (codmat, nce, date.fromisoformat(jour)))
    if absence is None:
        abort(404)
    db.session.delete(absence)
    db.session.commit()
    flash('Absence supprimée.', 'success')
    return redirect(url_for('absences_etudiant', nce=nce))


# ================= INSCRIPTION (ouverte à tous : rôle 'user') =================
@app.route('/user/add', methods=['GET', 'POST'])
def add_user():
    form = UserForm()
    if form.validate_on_submit():
        user = User(username=form.username.data,
                    email=form.email.data,
                    password=pbkdf2_sha256.hash(form.password.data),  # mot de passe hashé
                    role='user')                                     # jamais admin par inscription
        db.session.add(user)
        db.session.commit()
        flash('Compte créé avec succès. Vous pouvez vous connecter.', 'success')
        return redirect(url_for('login'))
    return render_template('add_user.html', form=form)


if __name__ == '__main__':
    app.run(debug=True)
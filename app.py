from datetime import date

from flask import Flask, render_template, redirect, url_for, flash, abort
from flask_wtf.csrf import CSRFProtect
from passlib.hash import pbkdf2_sha256

from config import Config
from extensions import db, migrate
from models import User, Classe, Etudiant, Matiere, Absence
from forms import UserForm, ClasseForm, EtudiantForm, MatiereForm, AbsenceForm
from admin_views import init_admin
app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
migrate.init_app(app, db)
csrf = CSRFProtect(app)   # protège aussi les boutons "Supprimer" (POST)
init_admin(app, csrf)  # interface /admin (Flask-Admin)
app.app_context().push()  # contexte d'application hors requête HTTP (TD, Partie 1 - point 2)


def maj_effectif(cod_class):
    """Recalcule NbrEtud (nombre d'étudiants) d'une classe."""
    classe = db.session.get(Classe, cod_class)
    if classe:
        classe.NbrEtud = Etudiant.query.filter_by(CodClass=cod_class).count()
        db.session.commit()


# ================= ÉTUDIANTS (page d'accueil) =================
@app.route('/')
def index():
    etudiants = Etudiant.query.order_by(Etudiant.Nom).all()
    return render_template('index.html', etudiants=etudiants)


@app.route('/etudiant/add', methods=['GET', 'POST'])
def add_etudiant():
    classes = Classe.query.order_by(Classe.CodClass).all()
    if not classes:
        flash("Ajoutez d'abord une classe.", 'danger')
        return redirect(url_for('list_classes'))

    form = EtudiantForm()
    form.CodClass.choices = [(c.CodClass, f'{c.CodClass} - {c.NomClass}') for c in classes]

    if form.validate_on_submit():
        db.session.add(Etudiant(NCE=form.NCE.data.strip(),
                                Nom=form.Nom.data.strip(),
                                Prenom=form.Prenom.data.strip(),
                                DateNais=form.DateNais.data,
                                LieuNais=(form.LieuNais.data or '').strip() or None,
                                CodClass=form.CodClass.data))
        db.session.commit()
        maj_effectif(form.CodClass.data)
        flash('Étudiant ajouté.', 'success')
        return redirect(url_for('index'))
    return render_template('add_etudiant.html', form=form)


@app.route('/etudiant/<nce>/delete', methods=['POST'])
def delete_etudiant(nce):
    etudiant = db.get_or_404(Etudiant, nce)
    cod_class = etudiant.CodClass
    db.session.delete(etudiant)   # ses absences sont supprimées aussi
    db.session.commit()
    maj_effectif(cod_class)
    flash('Étudiant supprimé (et ses absences).', 'success')
    return redirect(url_for('index'))


# ================= CLASSES =================
@app.route('/classes', methods=['GET', 'POST'])
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
def delete_classe(cod):
    classe = db.get_or_404(Classe, cod)
    db.session.delete(classe)     # ses étudiants et leurs absences sont supprimés aussi
    db.session.commit()
    flash('Classe supprimée (avec ses étudiants et leurs absences).', 'success')
    return redirect(url_for('list_classes'))


# ================= MATIÈRES =================
@app.route('/matieres', methods=['GET', 'POST'])
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
def delete_matiere(cod):
    matiere = db.get_or_404(Matiere, cod)
    db.session.delete(matiere)    # ses absences sont supprimées aussi
    db.session.commit()
    flash('Matière supprimée (et ses absences).', 'success')
    return redirect(url_for('list_matieres'))


# ================= ABSENCES =================
@app.route('/absences/<nce>')
def absences_etudiant(nce):
    etudiant = db.get_or_404(Etudiant, nce)
    absences = (Absence.query.filter_by(NCE=nce)
                .order_by(Absence.DateA).all())
    return render_template('absece_Etudiant.html', etudiant=etudiant, absences=absences)


@app.route('/absence/add', methods=['GET', 'POST'])
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
def delete_absence(codmat, nce, jour):
    absence = db.session.get(Absence, (codmat, nce, date.fromisoformat(jour)))
    if absence is None:
        abort(404)
    db.session.delete(absence)
    db.session.commit()
    flash('Absence supprimée.', 'success')
    return redirect(url_for('absences_etudiant', nce=nce))


# ================= UTILISATEUR (TD Partie 1 - points 3 et 4) =================
@app.route('/user/add', methods=['GET', 'POST'])
def add_user():
    form = UserForm()
    if form.validate_on_submit():
        user = User(username=form.username.data,
                    email=form.email.data,
                    password=pbkdf2_sha256.hash(form.password.data))  # mot de passe hashé
        db.session.add(user)
        db.session.commit()
        flash('Utilisateur ajouté avec succès.', 'success')
        return redirect(url_for('index'))
    return render_template('add_user.html', form=form)


if __name__ == '__main__':
    app.run(debug=True)
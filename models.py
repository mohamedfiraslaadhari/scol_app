from extensions import db


class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)

    def __str__(self):
        return self.username


class Classe(db.Model):
    __tablename__ = 'classe'
    CodClass = db.Column(db.String(20), primary_key=True)
    NomClass = db.Column(db.String(50), nullable=False)
    NbrEtud = db.Column(db.Integer, default=0)

    etudiants = db.relationship('Etudiant', back_populates='classe',
                                cascade='all, delete-orphan', passive_deletes=True)

    def __str__(self):
        return f'{self.CodClass} - {self.NomClass}'


class Etudiant(db.Model):
    __tablename__ = 'etudiant'
    NCE = db.Column(db.String(20), primary_key=True)
    Nom = db.Column(db.String(50), nullable=False)
    Prenom = db.Column(db.String(50), nullable=False)
    DateNais = db.Column(db.Date)
    LieuNais = db.Column(db.String(50))
    photo = db.Column(db.String(255))  # nom du fichier image (TD3)
    CodClass = db.Column(
        db.String(20),
        db.ForeignKey('classe.CodClass', onupdate='CASCADE', ondelete='CASCADE'),
        nullable=False)

    classe = db.relationship('Classe', back_populates='etudiants')
    absences = db.relationship('Absence', back_populates='etudiant',
                               cascade='all, delete-orphan', passive_deletes=True)

    def __str__(self):
        return f'{self.NCE} - {self.Nom} {self.Prenom}'


class Matiere(db.Model):
    __tablename__ = 'matiere'
    CodMat = db.Column(db.String(20), primary_key=True)
    IntMat = db.Column(db.String(100), nullable=False)
    Description = db.Column(db.Text)

    absences = db.relationship('Absence', back_populates='matiere',
                               cascade='all, delete-orphan', passive_deletes=True)

    def __str__(self):
        return f'{self.CodMat} - {self.IntMat}'


class Absence(db.Model):
    __tablename__ = 'absence'
    # Clé primaire composée : (CodMat, NCE, DateA)
    CodMat = db.Column(
        db.String(20),
        db.ForeignKey('matiere.CodMat', onupdate='CASCADE', ondelete='CASCADE'),
        primary_key=True)
    NCE = db.Column(
        db.String(20),
        db.ForeignKey('etudiant.NCE', onupdate='CASCADE', ondelete='CASCADE'),
        primary_key=True)
    DateA = db.Column(db.Date, primary_key=True)
    NHA = db.Column(db.Float, nullable=False)  # 1.45 = 1h45

    etudiant = db.relationship('Etudiant', back_populates='absences')
    matiere = db.relationship('Matiere', back_populates='absences')

    def __str__(self):
        return f'{self.NCE} / {self.CodMat} / {self.DateA}'
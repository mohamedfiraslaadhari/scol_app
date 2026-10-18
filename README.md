# Gestion des absences scolaires (Flask + PostgreSQL)

TD-TP **Gestion de données avec Flask** : application web de gestion des classes, des matières, des étudiants et de leurs absences, avec une interface d'administration **Flask-Admin** (TD2).

Module : Développement web avec Python, cycle ingénieur en informatique (INGTA2-S1).

## Fonctionnalités

- Ajouter et supprimer des **classes**, des **matières** et des **étudiants**
- Enregistrer et supprimer les **absences** d'un étudiant (NHA : 1.45 = 1h45)
- Afficher, pour un étudiant, la liste de ses absences (date, matière, nombre d'heures)
- Ajouter un **utilisateur** avec mot de passe hashé (Passlib)
- Formulaires **Flask-WTF** avec validation et protection CSRF
- Migrations de base de données avec **Flask-Migrate**
- **Interface d'administration Flask-Admin** (`/admin`) : gestion des utilisateurs, classes, étudiants, matières et absences (TD2)

## Technologies

Python 3.12, Flask, Flask-SQLAlchemy, Flask-Migrate, Flask-WTF, **Flask-Admin**, **Flask-Babel**, PostgreSQL (psycopg2), Passlib, Jinja2.

## Schéma de la base de données

```
Classe   (CodClass, NomClass, NbrEtud)
Etudiant (NCE, Nom, Prenom, DateNais, LieuNais, #CodClass)
Matiere  (CodMat, IntMat, Description)
Absence  (#CodMat, #NCE, DateA, NHA)
User     (id, username, email, password)
```

Contraintes d'intégrité : les clés étrangères utilisent `ON UPDATE CASCADE` et `ON DELETE CASCADE`. Supprimer une classe supprime ses étudiants et leurs absences ; supprimer une matière supprime ses absences.

## Structure du projet

```
scol_app/
├── app.py            # application et routes
├── admin_views.py    # interface d'administration Flask-Admin (TD2)
├── config.py         # configuration (lit le fichier .env)
├── extensions.py     # db et migrate
├── models.py         # modèles SQLAlchemy
├── forms.py          # formulaires Flask-WTF
├── requirements.txt
├── migrations/       # migrations Flask-Migrate
├── static/css/
└── templates/        # pages Jinja2
```

## Installation

1. Cloner le dépôt :

```
git clone https://github.com/mohamedfiraslaadhari/scol_app.git
cd scol_app
```

2. Créer et activer l'environnement virtuel (Windows) :

```
python -m venv monvenv
monvenv\Scripts\activate
```

3. Installer les dépendances :

```
pip install -r requirements.txt
```

4. Créer la base PostgreSQL `scol` (par exemple dans pgAdmin) :

```
CREATE DATABASE scol;
```

5. Créer un fichier `.env` à la racine du projet avec le mot de passe PostgreSQL :

```
DB_PASSWORD=votre_mot_de_passe
```

Les autres paramètres (utilisateur `postgres`, hôte `localhost`, port `5432`, base `scol`) se changent aussi avec `DB_USER`, `DB_HOST`, `DB_PORT` et `DB_NAME`.

6. Créer les tables :

```
flask db upgrade
```

7. Lancer l'application :

```
python app.py
```

Puis ouvrir <http://127.0.0.1:5000>

## Pages principales

| Adresse           | Description                                   |
| ----------------- | --------------------------------------------- |
| `/`               | Liste des étudiants                           |
| `/etudiant/add`   | Ajouter un étudiant                           |
| `/classes`        | Gérer les classes                             |
| `/matieres`       | Gérer les matières                            |
| `/absence/add`    | Ajouter une absence                           |
| `/absences/<NCE>` | Absences d'un étudiant                        |
| `/user/add`       | Ajouter un utilisateur                        |
| `/admin`          | Interface d'administration Flask-Admin (TD2)  |

## TD2 : Interface d'administration (Flask-Admin)

L'interface `/admin` propose cinq vues : **User, Classe, Etudiant, Matiere, Absence**.

- **User** : formulaire avec validation (username de 4 à 20 caractères, email valide, mot de passe de 6 caractères minimum). Le mot de passe est haché avec Passlib et n'est jamais affiché dans la liste. En modification, un mot de passe laissé vide conserve l'ancien.
- **Classe** : le nombre d'étudiants est calculé automatiquement.
- **Etudiant** : la classe est choisie dans une liste déroulante, avec recherche et filtre par classe.
- **Matiere** : recherche par code ou intitulé.
- **Absence** : l'étudiant et la matière sont choisis dans des listes déroulantes.
- **Contraintes d'intégrité** : suppression en cascade (classe → étudiants → absences).
- **Flask-Babel** est initialisé pour la traduction de l'interface.
## TD3 : Téléchargement de fichiers (Flask-Uploads)

- Champ **photo** ajouté au modèle `Etudiant` (migration Flask-Migrate).
- Bibliothèque **Flask-Reuploaded** (compatible avec les Flask récents, même `import flask_uploads`).
- Ajout d'un étudiant avec photo : types autorisés `jpg`, `jpeg`, `png`, `gif`, taille maximale 2 Mo. L'image est enregistrée dans `static/image/` sous le nom `<NCE>.<extension>`.
- Page de **modification** `/etudiant/<NCE>/edit` : affiche la photo actuelle, la conserve si aucune nouvelle image n'est choisie, et supprime l'ancienne en cas de remplacement.
- **Suppression** d'un étudiant (bouton avec confirmation, requête POST protégée par CSRF) : supprime aussi sa photo et gère `IntegrityError`.
- Icônes **Font Awesome** pour les boutons Modifier et Supprimer.
- - Le dossier `static/image/` est ignoré par Git (photos = données personnelles).
## TP : Authentification et rôles (Flask-Login)

- **Flask-Login** : `LoginManager`, `UserMixin`, `user_loader`, `login_user` / `logout_user`, `@login_required`.
- Page de **connexion** `/login` (mot de passe vérifié avec Passlib) et **déconnexion** `/logout`.
- **Inscription** `/user/add` : crée toujours un compte avec le rôle `user`.
- **Rôles** (colonne `role` du modèle `User`) : `admin` et `user`.
  - `user` : consulter les étudiants et leurs absences, ajouter une absence.
  - `admin` : tout le reste (étudiants, classes, matières, suppressions) et l'interface `/admin`.
- Le menu change selon l'utilisateur connecté (`current_user.is_authenticated`, `current_user.is_admin()`).
- L'interface **Flask-Admin** est réservée aux administrateurs et propose des liens « Retour à l'application » et « Déconnexion ».
- Le rôle d'un utilisateur se modifie dans `/admin` → User.
## Auteur

Mohamed Firas Laâdhari
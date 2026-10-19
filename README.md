# Gestion des absences scolaires (Flask + PostgreSQL)

Application web de gestion des classes, des matières, des étudiants et de leurs absences, développée dans le cadre du module **Développement web avec Python** (cycle ingénieur en informatique, INGTA2-S1). Elle regroupe les TD (Flask-Admin, Flask-Uploads), le TP Flask-Login et les ajouts du mini-projet : API REST, tableau de bord et sécurité.

## Fonctionnalités

- Gestion des **classes**, des **matières** et des **étudiants** (ajout, modification, suppression)
- Enregistrement et consultation des **absences** d'un étudiant (NHA : 1.45 = 1h45)
- **Photo** de l'étudiant (upload d'image)
- **Connexion / déconnexion** avec deux rôles : `admin` et `user`
- **API REST** en JSON (`/api/...`)
- **Tableau de bord** avec statistiques et états (`/dashboard`)
- **Interface d'administration Flask-Admin** (`/admin`), réservée aux administrateurs
- Formulaires **Flask-WTF** avec validation, mots de passe hachés (**Passlib**), migrations **Flask-Migrate**

## Technologies

Python 3.12, Flask, Flask-SQLAlchemy, Flask-Migrate, Flask-WTF, Flask-Admin, Flask-Babel, Flask-Login, Flask-Reuploaded, PostgreSQL (psycopg2), Passlib, Jinja2.

## Schéma de la base de données

```
Classe   (CodClass, NomClass, NbrEtud)
Etudiant (NCE, Nom, Prenom, DateNais, LieuNais, photo, #CodClass)
Matiere  (CodMat, IntMat, Description)
Absence  (#CodMat, #NCE, DateA, NHA)
User     (id, username, email, password, role)
```

Contraintes d'intégrité : les clés étrangères utilisent `ON UPDATE CASCADE` et `ON DELETE CASCADE`. Supprimer une classe supprime ses étudiants et leurs absences ; supprimer une matière supprime ses absences.

## Structure du projet

```
scol_app/
├── app.py            # application et routes
├── api.py            # API REST (Blueprint)
├── dashboard.py      # tableau de bord (Blueprint)
├── securite.py       # en-têtes HTTP, cookies, limitation des connexions
├── admin_views.py    # interface d'administration Flask-Admin
├── config.py         # configuration (lit le fichier .env)
├── extensions.py     # db et migrate
├── models.py         # modèles SQLAlchemy
├── forms.py          # formulaires Flask-WTF
├── requirements.txt
├── migrations/       # migrations Flask-Migrate
├── static/
│   ├── css/
│   └── image/        # photos des étudiants
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

8. Créer un compte avec la page **Inscription**, puis le passer administrateur :

```
python -c "from app import db; from models import User; u = User.query.filter_by(username='VOTRE_NOM').first(); u.role = 'admin'; db.session.commit()"
```

## Pages principales

| Adresse                | Rôle requis | Description                            |
| ---------------------- | ----------- | -------------------------------------- |
| `/login`               | aucun       | Connexion                              |
| `/user/add`            | aucun       | Inscription (compte `user`)            |
| `/logout`              | connecté    | Déconnexion                            |
| `/`                    | connecté    | Liste des étudiants                    |
| `/dashboard`           | connecté    | Tableau de bord                        |
| `/absences/<NCE>`      | connecté    | Absences d'un étudiant                 |
| `/absence/add`         | connecté    | Ajouter une absence                    |
| `/etudiant/add`        | `admin`     | Ajouter un étudiant (avec photo)       |
| `/etudiant/<NCE>/edit` | `admin`     | Modifier un étudiant et sa photo       |
| `/classes`             | `admin`     | Gérer les classes                      |
| `/matieres`            | `admin`     | Gérer les matières                     |
| `/admin`               | `admin`     | Interface d'administration Flask-Admin |

## API REST

Toutes les routes renvoient du JSON et demandent d'être connecté (sinon `401`).

| Route                            | Description                                  |
| -------------------------------- | -------------------------------------------- |
| `GET /api/etudiants`             | Liste des étudiants                          |
| `GET /api/etudiants/<nce>`       | Fiche d'un étudiant                          |
| `GET /api/etudiants/<nce>/absences` | Absences d'un étudiant et total d'heures  |
| `GET /api/classes`               | Liste des classes                            |
| `GET /api/classes/<code>`        | Une classe avec ses étudiants                |
| `GET /api/matieres`              | Liste des matières                           |
| `GET /api/absences`              | Liste des absences                           |
| `GET /api/stats`                 | Compteurs généraux                           |
| `GET /api/users`                 | Liste des utilisateurs (admin uniquement, `403` sinon, sans mot de passe) |

## Tableau de bord

La page `/dashboard` affiche des compteurs (classes, étudiants, matières, absences, total d'heures), un graphique du nombre d'étudiants par classe, un graphique des heures d'absence par matière, le classement des 5 étudiants les plus absents (statut **Alerte** à partir de 10 h d'absence) et les 5 dernières absences.

## Sécurité

- **Protection CSRF** de tous les formulaires et boutons de suppression (Flask-WTF).
- **Mots de passe hachés** avec Passlib (`pbkdf2_sha256`), jamais affichés ni renvoyés par l'API.
- **Authentification** Flask-Login et **rôles** (`admin` / `user`) : routes protégées par `@login_required` et un décorateur `admin_required`.
- **Interface Flask-Admin** et **API** protégées : accès refusé sans connexion, ou sans le rôle requis.
- **Redirection `next` contrôlée** : seules les adresses internes sont acceptées.
- **Limitation des tentatives de connexion** : après 5 échecs en 5 minutes pour un même identifiant et une même adresse IP, la connexion est bloquée temporairement.
- **En-têtes de sécurité HTTP** : `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, `Permissions-Policy` (et `Strict-Transport-Security` en HTTPS).
- **Cookies de session** `HttpOnly` et `SameSite=Lax`. L'option `Secure` s'active avec la variable d'environnement `COOKIES_SECURISES=1` (à utiliser derrière HTTPS).
- **Requêtes SQL paramétrées** (ORM SQLAlchemy).
- **Fichiers téléversés** : types limités (`jpg`, `jpeg`, `png`, `gif`), taille maximale 2 Mo, nom de fichier contrôlé.

## TD2 : Interface d'administration (Flask-Admin)

L'interface `/admin` propose cinq vues : **User, Classe, Etudiant, Matiere, Absence**, avec des liens « Retour à l'application » et « Déconnexion ».

- **User** : validation (username de 4 à 20 caractères, email valide, mot de passe de 6 caractères minimum), mot de passe haché, rôle choisi dans une liste.
- **Classe** : le nombre d'étudiants est calculé automatiquement.
- **Etudiant** : classe choisie dans une liste déroulante, recherche et filtre par classe.
- **Matiere** et **Absence** : recherche, filtres, listes déroulantes.
- **Flask-Babel** est initialisé pour la traduction de l'interface.

## TD3 : Téléchargement de fichiers (Flask-Uploads)

- Champ **photo** ajouté au modèle `Etudiant` (migration Flask-Migrate).
- Bibliothèque **Flask-Reuploaded** (compatible avec les Flask récents, même `import flask_uploads`).
- Ajout d'un étudiant avec photo : image enregistrée dans `static/image/` sous le nom `<NCE>.<extension>`.
- Page de **modification** : affiche la photo actuelle, la conserve si aucune nouvelle image n'est choisie, et supprime l'ancienne en cas de remplacement.
- **Suppression** d'un étudiant (confirmation, requête POST) : supprime aussi sa photo et gère `IntegrityError`.

## TP : Authentification et rôles (Flask-Login)

- `LoginManager`, `UserMixin`, `user_loader`, `login_user` / `logout_user`, `@login_required`.
- `user` : consulter les étudiants, le tableau de bord et les absences, ajouter une absence.
- `admin` : tout le reste (étudiants, classes, matières, suppressions) et `/admin`.
- Le menu change selon l'utilisateur connecté (`current_user.is_authenticated`, `current_user.is_admin()`).
- L'inscription crée toujours un compte `user` ; le rôle se modifie dans `/admin` → User.

## Auteur

Mohamed Firas Laâdhari
# Gestion des absences scolaires (Flask + PostgreSQL)

TD-TP **Gestion de données avec Flask** : application web de gestion des classes, des matières, des étudiants et de leurs absences.

Module : Développement web avec Python, cycle ingénieur en informatique (INGTA2-S1).

## Fonctionnalités

- Ajouter et supprimer des **classes**, des **matières** et des **étudiants**
- Enregistrer et supprimer les **absences** d'un étudiant (NHA : 1.45 = 1h45)
- Afficher, pour un étudiant, la liste de ses absences (date, matière, nombre d'heures)
- Ajouter un **utilisateur** avec mot de passe hashé (Passlib)
- Formulaires **Flask-WTF** avec validation et protection CSRF
- Migrations de base de données avec **Flask-Migrate**

## Technologies

Python 3.12, Flask, Flask-SQLAlchemy, Flask-Migrate, Flask-WTF, PostgreSQL (psycopg2), Passlib, Jinja2.

## Schéma de la base de données

```
Classe   (CodClass, NomClass, NbrEtud)
Etudiant (NCE, Nom, Prenom, DateNais, LieuNais, #CodClass)
Matiere  (CodMat, IntMat, Description)
Absence  (#CodMat, #NCE, DateA, NHA)
User     (id, username, email, password)
```

## Structure du projet

```
scol_app/
├── app.py            # application et routes
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

```sql
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

Puis ouvrir http://127.0.0.1:5000

## Pages principales

| Adresse | Description |
|---|---|
| `/` | Liste des étudiants |
| `/etudiant/add` | Ajouter un étudiant |
| `/classes` | Gérer les classes |
| `/matieres` | Gérer les matières |
| `/absence/add` | Ajouter une absence |
| `/absences/<NCE>` | Absences d'un étudiant |
| `/user/add` | Ajouter un utilisateur |

## Auteur

Mohamed Firas Laâdhari
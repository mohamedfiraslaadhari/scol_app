from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

# Objets créés ici (sans app) pour éviter les imports circulaires.
# Ils sont reliés à l'application dans app.py avec init_app().
db = SQLAlchemy()
migrate = Migrate()

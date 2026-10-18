import os
from pathlib import Path
from dotenv import load_dotenv

# lit le fichier .env placé à côté de ce fichier (non envoyé sur GitHub)
load_dotenv(Path(__file__).resolve().parent / '.env', override=True)

# --- Paramètres PostgreSQL ---
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'YOUR_PASSWORD')
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = os.getenv('DB_NAME', 'scol')


class Config:
    SQLALCHEMY_DATABASE_URI = (
        f'postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.getenv('SECRET_KEY', 'change-me-in-production')  # requis par Flask-WTF (CSRF)
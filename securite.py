"""Sécurité (Mini-projet) : en-têtes HTTP, cookies de session, limitation des connexions."""
import os
import time
from collections import defaultdict, deque
from threading import Lock

from flask import request

MAX_ECHECS = 5     # nombre d'échecs autorisés...
FENETRE = 300      # ... pendant 5 minutes (en secondes)

_echecs = defaultdict(deque)   # clé -> horodatages des échecs récents
_verrou = Lock()


def cle_connexion(identifiant):
    """Clé de limitation : identifiant saisi + adresse IP du visiteur."""
    return f'{(identifiant or "").strip().lower()}|{request.remote_addr}'


def secondes_restantes(cle):
    """0 si la connexion est autorisée, sinon le nombre de secondes à attendre."""
    maintenant = time.time()
    with _verrou:
        file = _echecs[cle]
        while file and maintenant - file[0] > FENETRE:
            file.popleft()                      # on oublie les échecs trop anciens
        if len(file) >= MAX_ECHECS:
            return int(FENETRE - (maintenant - file[0])) + 1
        return 0


def enregistrer_echec(cle):
    with _verrou:
        _echecs[cle].append(time.time())


def reinitialiser_echecs(cle):
    with _verrou:
        _echecs.pop(cle, None)


def init_securite(app):
    """Configure les cookies de session et les en-têtes de sécurité HTTP."""
    en_https = os.environ.get('COOKIES_SECURISES') == '1'
    app.config.update(
        SESSION_COOKIE_HTTPONLY=True,       # cookie inaccessible depuis JavaScript
        SESSION_COOKIE_SAMESITE='Lax',      # non envoyé lors de requêtes inter-sites
        SESSION_COOKIE_SECURE=en_https,     # HTTPS uniquement (si activé)
        REMEMBER_COOKIE_HTTPONLY=True,
        REMEMBER_COOKIE_SAMESITE='Lax',
        REMEMBER_COOKIE_SECURE=en_https,
    )

    @app.after_request
    def ajouter_en_tetes(reponse):
        reponse.headers.setdefault('X-Content-Type-Options', 'nosniff')
        reponse.headers.setdefault('X-Frame-Options', 'SAMEORIGIN')       # anti-clickjacking
        reponse.headers.setdefault('Referrer-Policy', 'strict-origin-when-cross-origin')
        reponse.headers.setdefault('Permissions-Policy',
                                   'camera=(), microphone=(), geolocation=()')
        if request.is_secure:
            reponse.headers.setdefault('Strict-Transport-Security',
                                       'max-age=31536000; includeSubDomains')
        return reponse
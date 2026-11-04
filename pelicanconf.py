
# -*- coding: utf-8 -*- #

# Informations générales sur le site
SITENAME = "Famille Burais"
SITEURL = ""  # Laisser vide pour le développement local
AUTHOR = 'famille@burais.fr'

PATH = "content"
TIMEZONE = "Europe/Paris"
DEFAULT_LANG = "fr"
# Articles without a Date (e.g. a trip with no dated footprint) fall back to the file mtime.
DEFAULT_DATE = "fs"

# ==========================================
# CONFIGURATION DU DOSSIER DE THÈME MAÎTRE
# ==========================================
# On pointe vers le dossier global qui abrite tous nos templates personnalisés
THEME = "themes/global"

# Variable interne de Pelican pour l'emplacement des fichiers statiques générés
# Par défaut, Pelican crée un dossier 'theme' dans le dossier de sortie ('output/theme')
THEME_STATIC_DIR = "theme"

# ==========================================
# GESTION DES ACTIFS STATIQUES (MÉTIER)
# ==========================================
# On demande à Pelican de copier fidèlement l'intégralité du contenu du dossier static du thème.
# Cela garantit que 'theme/burais/images/bg-home.jpg' et 'theme/burais/css/main.css' 
# seront accessibles hors-ligne et localement par vos templates HTML.
# "pages" and "articles" are included so media are copied next to their generated pages
# (FindPenguins trip/footprint articles carry their photos and videos).
STATIC_PATHS = ["images", "pages", "articles"]

# ==========================================
# CONFIGURATION DES PAGES ET DES URLS
# ==========================================
# Configuration pour s'assurer que la page d'accueil (index.html) soit générée proprement 
# à partir de votre fichier Markdown 'home.md' sans interférence avec les articles de blog.
PLUGIN_PATHS = ["plugins"]
PLUGINS = ["flat_pages", "wikilinks", "fontawesome", "weasypdf"]
# Output mirrors content/pages (see plugins/flat_pages.py); explicit Save_as still wins.
PAGE_URL = "{slug}.html"
PAGE_SAVE_AS = "{slug}.html"

# Désactiver les flux RSS/Atom pour le développement local
FEED_ALL_ATOM = None
CATEGORY_FEED_ATOM = None
TRANSLATION_FEED_ATOM = None
AUTHOR_FEED_ATOM = None
AUTHOR_FEED_RSS = None

# Liens de navigation (optionnel, vide pour coller au minimalisme de Burais)
LINKS = ()
SOCIAL = ()

# Nombre d'éléments par page si vous utilisez un autre thème de type blog
DEFAULT_PAGINATION = 10

# Conserver la structure des dossiers lors de la génération
# Kept False: rmtree of output/ races with autoreload (-r) while the scraper writes files.
# Use `make clean` to wipe stale output.
DELETE_OUTPUT_DIRECTORY = True

import math

JINJA_FILTERS = {
    'count_to_font_size': lambda c: '{p:.1f}%'.format(p=100 + 25 * math.log(c, 2)),
}

import os

# Vos autres configurations (SITENAME, PATH, etc.)

# Fonction pour tester si le fichier existe sur le disque
def file_exists(relative_path):
    # 'PATH' correspond généralement à votre dossier 'content/'
    # Adaptez le chemin selon l'endroit réel où se trouvent vos images lors du build
    full_path = os.path.join(os.path.dirname(__file__), 'content', relative_path)
    return os.path.exists(full_path)

# Enregistrement de la fonction dans les variables globales de Jinja
JINJA_GLOBALS = {
    'file_exists': file_exists
}

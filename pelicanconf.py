
# -*- coding: utf-8 -*- #

# Informations générales sur le site
SITENAME = "Famille Burais"
SITEURL = ""  # Laisser vide pour le développement local
AUTHOR = 'famille@burais.fr'

PATH = "content"
TIMEZONE = "Europe/Paris"
DEFAULT_LANG = "fr"

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
STATIC_PATHS = ["images"]

# ==========================================
# CONFIGURATION DES PAGES ET DES URLS
# ==========================================
# Configuration pour s'assurer que la page d'accueil (index.html) soit générée proprement 
# à partir de votre fichier Markdown 'home.md' sans interférence avec les articles de blog.
PAGE_URL = "pages/{slug}.html"
PAGE_SAVE_AS = "pages/{slug}.html"

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
DELETE_OUTPUT_DIRECTORY = True


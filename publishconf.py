# -*- coding: utf-8 -*- #
import os
import sys

# Assurer que Pelican trouve les configurations de base
sys.path.append(os.path.dirname(__file__))
from pelicanconf import *

# ==========================================
# DÉTECTION ET CONFIGURATION DE SITEURL
# ==========================================
# On regarde si une variable d'environnement 'DEPLOY_TARGET' est définie.
# Si c'est 'github', on applique l'URL GitHub Pages, sinon on applique l'URL OVH.

if os.environ.get("DEPLOY_TARGET") == "github":
    # ⚠️ Remplacez par votre pseudo et le nom de votre dépôt GitHub
    SITEURL = "https://lburais.github.io/website"
else:
    # ⚠️ Remplacez par votre nom de domaine final chez OVH
    SITEURL = "https://burais.fr"

# Forcer la génération des liens absolus en production pour éviter les images cassées
RELATIVE_URLS = False

# ==========================================
# CONFIGURATIONS DE PRODUCTION COMPLÉMENTAIRES
# ==========================================
# Activer le nettoyage complet du dossier de sortie avant génération
DELETE_OUTPUT_DIRECTORY = True

# Désactiver les configurations spécifiques au développement (flux RSS de test, etc.)
FEED_ALL_ATOM = "feeds/all.atom.xml"
CATEGORY_FEED_ATOM = "feeds/{slug}.atom.xml"

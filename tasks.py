import os
import shlex
import shutil
import sys
import datetime
from ftplib import FTP

from invoke import task
from invoke.main import program
from pelican import main as pelican_main
from pelican.server import ComplexHTTPRequestHandler, RootedHTTPServer
from pelican.settings import DEFAULT_CONFIG, get_settings_from_file

# --- CHARGEMENT SÉCURISÉ DES SÉCRETS ---
from dotenv import load_dotenv
load_dotenv() # Lit le fichier .env s'il existe
# ----------------------------------------

OPEN_BROWSER_ON_SERVE = True
SETTINGS_FILE_BASE = "pelicanconf.py"
SETTINGS = {}
SETTINGS.update(DEFAULT_CONFIG)
LOCAL_SETTINGS = get_settings_from_file(SETTINGS_FILE_BASE)
SETTINGS.update(LOCAL_SETTINGS)

CONFIG = {
    "settings_base": SETTINGS_FILE_BASE,
    "settings_publish": "publishconf.py",
    # Output path. Can be absolute or relative to tasks.py. Default: 'output'
    "deploy_path": SETTINGS["OUTPUT_PATH"],
    # Github Pages configuration
    "github_pages_branch": "gh-pages", # Branche standard dédiée à l'hébergement GitHub Pages
    "commit_message": f"'Publish site on {datetime.date.today().isoformat()}'",
    # Host and port for `serve`
    "host": "localhost",
    "port": 8000,
    # ==========================================
    # CONFIGURATION FTP POUR OVH
    # ==========================================
    "ftp_host": os.getenv("OVH_FTP_HOST"),
    "ftp_user": os.getenv("OVH_FTP_USER"),
    "ftp_pass": os.getenv("OVH_FTP_PASS"),            
    "ftp_target_dir": os.getenv("OVH_FTP_DIR"),                       
}


@task
def clean(c):
    """Remove generated files"""
    if os.path.isdir(CONFIG["deploy_path"]):
        shutil.rmtree(CONFIG["deploy_path"])
        os.makedirs(CONFIG["deploy_path"])


@task
def build(c):
    """Build local version of site"""
    pelican_run("-s {settings_base}".format(**CONFIG))


@task
def rebuild(c):
    """`build` with the delete switch"""
    pelican_run("-d -s {settings_base}".format(**CONFIG))


@task
def regenerate(c):
    """Automatically regenerate site upon file modification"""
    pelican_run("-r -s {settings_base}".format(**CONFIG))


@task
def serve(c):
    """Serve site at http://HOST:PORT/ (default is localhost:8000)"""

    class AddressReuseTCPServer(RootedHTTPServer):
        allow_reuse_address = True

    server = AddressReuseTCPServer(
        CONFIG["deploy_path"],
        (CONFIG["host"], CONFIG["port"]),
        ComplexHTTPRequestHandler,
    )

    if OPEN_BROWSER_ON_SERVE:
        # Open site in default browser
        import webbrowser

        webbrowser.open("http://{host}:{port}".format(**CONFIG))

    sys.stderr.write("Serving at {host}:{port} ...\n".format(**CONFIG))
    server.serve_forever()


@task
def reserve(c):
    """`build`, then `serve`"""
    build(c)
    serve(c)


@task
def preview(c):
    """Build production version of site"""
    pelican_run("-s {settings_publish}".format(**CONFIG))

@task
def livereload(c):
    """Automatically reload browser tab upon file modification."""
    from livereload import Server

    def cached_build():
        cmd = "-s {settings_base} -e CACHE_CONTENT=true LOAD_CONTENT_CACHE=true"
        pelican_run(cmd.format(**CONFIG))

    cached_build()
    server = Server()
    theme_path = SETTINGS["THEME"]
    watched_globs = [
        CONFIG["settings_base"],
        f"{theme_path}/templates/**/*.html",
    ]

    content_file_extensions = [".md", ".rst"]
    for extension in content_file_extensions:
        content_glob = "{}/**/*{}".format(SETTINGS["PATH"], extension)
        watched_globs.append(content_glob)

    static_file_extensions = [".css", ".js"]
    for extension in static_file_extensions:
        static_file_glob = f"{theme_path}/static/**/*{extension}"
        watched_globs.append(static_file_glob)

    for glob in watched_globs:
        server.watch(glob, cached_build)

    if OPEN_BROWSER_ON_SERVE:
        # Open site in default browser
        import webbrowser

        webbrowser.open("http://{host}:{port}".format(**CONFIG))

    server.serve(host=CONFIG["host"], port=CONFIG["port"], root=CONFIG["deploy_path"])


@task
def ftp_upload(c):
    """Publish to production via FTP (OVH)"""
    print("-> Génération du site pour la production...")
    preview(c)

    local_dir = CONFIG["deploy_path"]
    
    if not os.path.exists(local_dir):
        print(f"Erreur : Le dossier {local_dir} n'existe pas.")
        return

    print(f"-> Connexion FTP à {CONFIG['ftp_host']}...")
    try:
        with FTP(CONFIG["ftp_host"]) as ftp:
            ftp.login(user=CONFIG["ftp_user"], passwd=CONFIG["ftp_pass"])
            ftp.cwd(CONFIG["ftp_target_dir"])

            def upload_directory(local_path):
                for item in os.listdir(local_path):
                    local_item_path = os.path.join(local_path, item)
                    if os.path.isfile(local_item_path):
                        with open(local_item_path, "rb") as f:
                            ftp.storbinary(f"STOR {item}", f)
                    elif os.path.isdir(local_item_path):
                        if item not in ftp.nlst():
                            ftp.mkd(item)
                        ftp.cwd(item)
                        upload_directory(local_item_path)
                        ftp.cwd("..")

            print("-> Début du transfert des fichiers sur OVH...")
            upload_directory(local_dir)
            print("-> Félicitations ! Votre site est en ligne sur OVH.")
    except Exception as e:
        print(f"Erreur lors du transfert FTP : {e}")


@task
def github_publish(c):
    """Publish to GitHub Pages using ghp-import"""
    # Étape 1 : Injecter la variable d'environnement pour publishconf.py
    print("-> Configuration de l'URL pour GitHub Pages...")
    os.environ["DEPLOY_TARGET"] = "github"

    # Étape 2 : Génération de la version de production
    print("-> Génération du site pour la production...")
    preview(c)
    
    # Étape 3 : Envoi vers GitHub
    print(f"-> Envoi vers la branche GitHub Pages '{CONFIG['github_pages_branch']}'...")
    c.run(
        "ghp-import -b {github_pages_branch} "
        "-m {commit_message} "
        "{deploy_path} -p".format(**CONFIG)
    )
    print("-> Félicitations ! Votre site est en ligne sur GitHub Pages.")


def pelican_run(cmd):
    cmd += " " + program.core.remainder  # allows to pass-through args to pelican
    pelican_main(shlex.split(cmd))

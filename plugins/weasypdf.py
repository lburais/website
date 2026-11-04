import os
import logging
from pathlib import Path
from pelican import signals
from weasyprint import HTML, CSS

# Désactive les logs d'information de WeasyPrint (Step 1, Step 2, etc.)
logging.getLogger('weasyprint').setLevel(logging.WARNING)

# Désactive également les logs très verbeux de la bibliothèque interne fontTools
logging.getLogger('fontTools').setLevel(logging.WARNING)
# ---------------------------------------------------------

logger = logging.getLogger(__name__)

def generate_articles_pdf(article_generator):
    """
    Filtre les articles 'trip' et leur concatène les articles 'footprint'
    situés dans leurs sous-dossiers respectifs.
    """
    output_path = article_generator.settings.get('OUTPUT_PATH', 'output')
    pdf_filename = article_generator.settings.get('WEASYPDF_FILENAME', 'voyages.pdf')
    pdf_stylesheet = article_generator.settings.get('WEASYPDF_STYLESHEET', None)
    
    all_articles = article_generator.articles
    if not all_articles:
        return

    # 1. Isoler les articles "findpenguins" 
    # (On vérifie ici si la catégorie est 'findpenguins', adaptable selon vos métadonnées)
    trip_articles = [a for a in all_articles if str(a.category).lower() == 'findpenguins']

    if not trip_articles:
        logger.info("[WeasyPDF] Aucun article 'findpenguins' trouvé. Génération ignorée.")
        return

    # 2. Structure pour stocker l'ordre final des articles à imprimer
    final_article_list = []

    for trip in trip_articles:
        # Ajouter le "trip" principal
        final_article_list.append(trip)
        
        # Trouver le dossier contenant cet article trip
        trip_file_path = Path(trip.source_path)
        trip_dir = trip_file_path.parent

        # Chercher les articles "footprint" dans les sous-dossiers de trip_dir
        footprints_du_trip = []
        for a in all_articles:
            if str(a.category).lower() == 'footprint':
                a_file_path = Path(a.source_path)
                
                # Vérifie si le fichier footprint est dans un sous-dossier strict du trip
                if a_file_path.is_relative_to(trip_dir) and a_file_path.parent != trip_dir:
                    footprints_du_trip.append(a)
        
        # Optionnel : Trier les footprints par date ou par nom de fichier
        footprints_du_trip.sort(key=lambda x: x.date)
        
        # Fusionner dans la liste finale après le trip parent
        final_article_list.extend(footprints_du_trip)

    logger.info(f"[WeasyPDF] {len(final_article_list)} articles retenus pour le PDF.")

    # 3. Construction du HTML
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Carnet de Voyage</title>
        <style>
            @page {
                size: A4; margin: 20mm;
                @bottom-right { content: counter(page); }
            }
            .page-toc, .article { page-break-after: always; }
            .article:last-child { page-break-after: avoid; }
            
            /* Style de la TOC */
            .toc-title { font-size: 28pt; margin-bottom: 30px; text-align: center; }
            .toc-list { list-style: none; padding: 0; }
            .toc-item { margin-bottom: 12px; font-size: 14pt; }
            .toc-item.indent { margin-left: 20px; font-size: 12pt; color: #555; } /* Indentation footprint */
            .toc-item a { text-decoration: none; color: black; display: flex; justify-content: space-between; }
            .toc-item a::after { content: target-counter(attr(href), page); font-weight: bold; }
            .toc-name { order: 1; }
            .toc-dots { order: 2; flex-grow: 1; border-bottom: 2px dotted #ccc; margin: 0 10px 4px 10px; }

            /* Style des articles */
            h1 { font-size: 24pt; margin-bottom: 5px; }
            .article.footprint h1 { font-size: 20pt; color: #2e7d32; } /* Style distinct pour les sous-articles */
            .metadata { color: #666; font-size: 10pt; margin-bottom: 20px; }
            .content img { max-width: 100%; height: auto; page-break-inside: avoid; }
        </style>
    </head>
    <body>
    """

    # 4. Génération de la Table des Matières (TOC) avec indentation visuelle
    html_content += """
    <div class="page-toc">
        <h1 class="toc-title">Sommaire du Voyage</h1>
        <ul class="toc-list">
    """
    for index, article in enumerate(final_article_list):
        is_footprint = str(article.category).lower() == 'footprint'
        indent_class = "indent" if is_footprint else ""
        prefix = "🐾 " if is_footprint else "📍 "
        
        html_content += f"""
            <li class="toc-item {indent_class}">
                <a href="#article-{index}">
                    <span class="toc-name">{prefix}{article.title}</span>
                    <span class="toc-dots"></span>
                </a>
            </li>
        """
    html_content += "</ul></div>"

    # 5. Injection du contenu HTML
    for index, article in enumerate(final_article_list):
        cat_lower = str(article.category).lower()
        
        html_content += f"""
        <div class="article {cat_lower}" id="article-{index}">
            <h1>{article.title}</h1>
            <div class="metadata">Date : {article.locale_date} | Type : {article.category}</div>
            <div class="content">
                {article.content}
            </div>
        </div>
        """

    html_content += "</body></html>"

    # 6. Rendu PDF
    try:
        final_pdf_path = os.path.join(output_path, pdf_filename)
        os.makedirs(output_path, exist_ok=True)
        wp_html = HTML(string=html_content, base_url=output_path)
        
        stylesheets = []
        if pdf_stylesheet and os.path.exists(pdf_stylesheet):
            stylesheets.append(CSS(pdf_stylesheet))

        wp_html.write_pdf(final_pdf_path, stylesheets=stylesheets)
        logger.info(f"[WeasyPDF] PDF généré : {final_pdf_path}")
    except Exception as e:
        logger.error(f"[WeasyPDF] Erreur : {e}")

def register():
    signals.article_generator_finalized.connect(generate_articles_pdf)

"""Mirror article and page source paths in the output."""
import logging
import os

from pelican import signals
from pelican.contents import Article, Page, Static

PREFIX = "pages/"
ARTICLE_PREFIX = "articles/"
TRIP_SERVICES = ("findpenguins", "polarsteps")
logger = logging.getLogger(__name__)


def _strip(path):
    path = path.replace(os.sep, "/")
    return path[len(PREFIX):] if path.startswith(PREFIX) else path


def relocate(obj):
    if isinstance(obj, Article):
        rel = obj.relative_source_path.replace(os.sep, "/")
        if not rel.startswith(ARTICLE_PREFIX) or "save_as" in obj.metadata:
            return
        rel = os.path.splitext(rel)[0] + ".html"
        obj.override_save_as = rel
        obj.override_url = rel
        # Trips without dated footprints have no EndDate: fall back to the article date so
        # templates can always sort trips by `enddate`.
        if str(obj.metadata.get("template")) in ("trip", "findpenguins_trip") and not hasattr(obj, "enddate"):
            obj.enddate = obj.date.strftime("%Y-%m-%d")
        return

    if not isinstance(obj, (Page, Static)):
        return
    rel = _strip(obj.relative_source_path)
    if isinstance(obj, Static) and rel.startswith("articles/findpenguins/flags/"):
        rel = rel[len("articles/findpenguins/"):]
    if isinstance(obj, Page):
        if "save_as" in obj.metadata:
            return
        rel = os.path.splitext(rel)[0] + ".html"
    obj.override_save_as = rel
    obj.override_url = rel


def link_footprints(generator):
    trips = {
        (os.path.dirname(article.relative_source_path.replace(os.sep, "/")), article.slug): article
        for article in generator.articles
        if str(article.category).lower() in TRIP_SERVICES
    }
    for article in generator.articles:
        source = article.relative_source_path.replace(os.sep, "/")
        if not any(source.startswith(f"articles/{service}/") for service in TRIP_SERVICES):
            continue
        if str(article.category).lower() != "footprint":
            continue
        trip_slug, separator, number = article.slug.rpartition("-etape-")
        trip_dir = os.path.dirname(os.path.dirname(source))
        trip = trips.get((trip_dir, trip_slug)) if separator and number.isdigit() else None
        if trip is None:
            logger.warning("No trip found for footprint %s in %s", article.slug, source)
            continue
        article.redirect_url = f"{trip.url}#{article.slug}"
        article.override_url = article.redirect_url
        article.template = "footprint_redirect"


class _TitleFilter(logging.Filter):
    # Generated pages carry their title in metadata and have no RST body heading.
    def filter(self, record):
        return "Document title missing" not in record.getMessage()


def register():
    logging.getLogger("pelican.readers").addFilter(_TitleFilter())
    signals.content_object_init.connect(relocate)
    signals.article_generator_finalized.connect(link_footprints)

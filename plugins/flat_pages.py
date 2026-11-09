"""Mirror article and page source paths in the output."""
import logging
import os

from pelican import signals
from pelican.contents import Article, Page, Static

PREFIX = "pages/"
ARTICLE_PREFIX = "articles/"


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
        if str(obj.metadata.get("template")) == "trip" and not hasattr(obj, "enddate"):
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


class _TitleFilter(logging.Filter):
    # Generated pages carry their title in metadata and have no RST body heading.
    def filter(self, record):
        return "Document title missing" not in record.getMessage()


def register():
    logging.getLogger("pelican.readers").addFilter(_TitleFilter())
    signals.content_object_init.connect(relocate)

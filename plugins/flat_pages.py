"""Mirror the content tree in the output, without the leading "pages/" level."""
import logging
import os

from pelican import signals
from pelican.contents import Page, Static

PREFIX = "pages/"


def _strip(path):
    path = path.replace(os.sep, "/")
    return path[len(PREFIX):] if path.startswith(PREFIX) else path


def relocate(obj):
    if not isinstance(obj, (Page, Static)):
        return
    rel = _strip(obj.relative_source_path)
    if isinstance(obj, Page):
        if "save_as" in obj.metadata:
            return
        if str(obj.category) == "Trips":
            obj.template = "trip"
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

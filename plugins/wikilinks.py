from pelican import signals

from functools import partial
from itertools import chain
import logging
from pathlib import Path
import re

logger = logging.getLogger(__name__)

__title__ = "minchin.pelican.plugins.wikilinks"
__version__ = "1.0.2-dev.1"
__description__ = "Support Wikilinks when generating Pelican sites."
__author__ = "W. Minchin"
__email__ = "w_minchin@hotmail.com"
__url__ = "http://blog.minchin.ca/label/wikilinks-pelican/"
__license__ = "MIT License"

LOG_PREFIX = "[Wikilinks]"

SOURCE_EXTS = tuple(
    [
        ".md",
        ".markdown",
        ".mkd",
        ".mdown",
        ".rst",
        ".rest",
        ".htm",
        ".html",
    ]
)

IMAGE_EXTS = tuple(
    [
        ".gif",
        ".tif",
        ".tiff",
        ".webp",
        ".jpg",
        ".jpeg",
        ".png",
        # ".pdf",
        ".svg",
    ]
)
VIDEO_EXTS = tuple(
    [
        ".mp4",
    ]
)
AUDIO_EXTS = tuple(
    [
        ".mp3",
        ".flac",
    ]
)
_OTHER_STATIC_EXTS = tuple(
    [
        ".pdf",
    ]
)

STATIC_EXTS = IMAGE_EXTS + VIDEO_EXTS + AUDIO_EXTS + _OTHER_STATIC_EXTS

GENERATOR_PAGE_LISTS = [
    "articles",
    "translations",
    "hidden_articles",
    "hidden_translations",
    "drafts",
    "draft_translations",
    "pages",
    "hidden_pages",
    "draft_pages",
    "staticfiles",
]

_base_wikilink_regex = (
    r"\[\[\s*(?P<filename>[^|\]]+)(\|\s*(?P<linkname>[^|\]\n\r]+))?\]\]"
)
wikilink_regex = re.compile(_base_wikilink_regex)
wikilink_file_regex = re.compile(r"!" + _base_wikilink_regex)

"""
# Test cases
[[my link]]
[[ my work ]]
[[ my work | is finished ]]

![[ a file.jpg ]]
![[file.jpg]]
"""


def _populate_link_pairs(generators):
    """
    Create a dictionary of filenames to final URLs.

    Needs to be run after the source material has been loaded into Pelican, so
    we can use Pelican's calculated URLs, rather than trying to guess what they
    should be.
    """
    logger.debug("%s Starting `populate_link_pairs()`.", LOG_PREFIX)
    # for `link_pairs`, the key is the filename (without extension) and the
    # value is the (final) URL that page will be found at.
    link_pairs = {}
    for generator in generators:

        target_list = []
        for my_item in GENERATOR_PAGE_LISTS:
            try:
                target_list.append(getattr(generator, my_item))
            except AttributeError:
                pass

        for file in chain(*target_list):
            # `file` is a `pelican.contents.Article`, etc

            # print(file, type(file))

            # `file.source_path` is a str
            try:
                link_pairs[Path(file.source_path).stem] = file.url
            except Exception as e:
                logger.error(
                    f'{LOG_PREFIX} Broke building list of link pairs: '
                    f'slug="{file.slug}" source_path="{file.source_path}" '
                    f'url="{file.url}"'
                )
                raise e

    # from pprint import pprint
    #
    # pprint(link_pairs)

    logger.info("%s %d link pairs found", LOG_PREFIX, len(link_pairs))

    return link_pairs


def _get_file_and_linkname(match):
    """
    Given a "raw" regex match, returns the cleaned up filename (key) and
    linkname (as displayed).
    """
    group = match.groupdict()
    filename = group["filename"].strip()
    linkname = group["linkname"] if group["linkname"] else filename
    linkname = linkname.strip()
    return filename, linkname


def _wikilink_replacement(link_pairs, SITEURL, match):
    filename, linkname = _get_file_and_linkname(match)
    # print(f"{filename=}, {linkname=}, {SITEURL=}, {link_pairs=}")
    path = link_pairs.get(filename)

    link_structure = (
        '<a href="{href}" class="wikilinks {wikilinks_class}">{linkname}</a>'.format(
            href=SITEURL + "/" + path if path else "#",
            wikilinks_class="wikilink-found" if path else "wikilink-missing",
            linkname=linkname,
        )
    )

    return link_structure


def _wikilink_file_replacement(link_pairs, SITEURL, match):
    filename, linkname = _get_file_and_linkname(match)

    path = link_pairs.get(filename)
    ext = Path(filename).suffix

    if ext in IMAGE_EXTS:
        link_structure_raw = (
            '<img src="{href}" class="wikilinks {wikilinks_class}" alt="{linkname}" />'
        )
    elif ext in AUDIO_EXTS:
        link_structure_raw = (
            '<audio control src="{href}" class="wikilinks {wikilinks_class}" />'
        )
    elif ext in VIDEO_EXTS:
        link_structure_raw = (
            '<video control src="{href}" class="wikilinks {wikilinks_class}" />'
        )
    else:
        link_structure_raw = (
            '<a href="{href}" class="wikilinks-file {wikilinks_class}">{linkname}</a>'
        )

    link_structure = link_structure_raw.format(
        href=SITEURL + "/" + path if path else "#",
        wikilinks_class="wikilink-found" if path else "wikilink-missing",
        linkname=linkname,
    )

    return link_structure


def replace_wikilinks(generators):
    """
    Given a text (i.e. the body of a article or a page), replaces all "raw"
    wikilinks within it, and returns the "fixed" text.

    Doesn't differentiate between wikilinks in the main body of those in code
    blocks, etc.
    """

    link_pairs = _populate_link_pairs(generators)

    for generator in generators:
        for my_item in GENERATOR_PAGE_LISTS:
            try:
                my_article_list = getattr(generator, my_item)
            except AttributeError:
                continue

            for my_article in my_article_list:
                SITEURL = my_article.settings["SITEURL"]

                _file_replacement = partial(
                    _wikilink_file_replacement, link_pairs, SITEURL
                )
                _link_replacement = partial(_wikilink_replacement, link_pairs, SITEURL)

                text = my_article._content
                if text:
                    text = wikilink_file_regex.sub(repl=_file_replacement, string=text)
                    text = wikilink_regex.sub(repl=_link_replacement, string=text)
                    my_article._content = text

    logger.info("%s complete!", LOG_PREFIX)

def register():
    """Register the plugin pieces with Pelican."""

    signals.all_generators_finalized.connect(replace_wikilinks)
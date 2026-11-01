# https://github.com/minchinweb/minchin.pelican.readers.tasknotes

from pelican import signals

# metadata
__title__ = "minchin.pelican.readers.tasknotes"
__version__ = "0.1.3-dev"
__description__ = "Tasknotes for Pelican"
__author__ = "W. Minchin"
__email__ = "w_minchin@hotmail.com"
__url__ = "https://blog.minchin.ca/label/tasknotes-pelican/"
__license__ = "MIT License"

# Configuration Defaults
LOG_PREFIX = "[TaskNotes]"

DEFAULT_TASKNOTES_CATEGORY = "tasks"

DEFAULT_IN_PROGRESS_STATUS = [
    "in-progress",
    "in progress",
    "20-in-progress",
]
DEFAULT_CANCELLED_STATUS = [
    "cancelled",
    "canceled",
    "50-cancelled",
]
DEFAULT_DUPLICATE_STATUS = [
    "duplicate",
    "60-duplicate",
]
DEFAULT_DONE_STATUS = [
    "done",
    "30-done",
]

from __future__ import annotations

import logging
import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pelican import Pelican
    from pelican.generators import ArticlesGenerator

from pelican.contents import Article

# from pelican.readers import MarkdownReader  # BaseReader
from pelican.utils import order_content

from minchin.pelican.readers.commonmark.reader import MDITReader

from .constants import DEFAULT_TASKNOTES_CATEGORY, LOG_PREFIX

# from pelican.utils import get_date, pelican_open


logger = logging.getLogger(__name__)

_tasknote_count = 0
_todotxt_lines = []


def addTaskNoteArticles(self: ArticlesGenerator) -> None:
    global _tasknote_count
    global _todotxt_lines

    settings = self.settings

    # Author, category, and tags are objects, not strings, so they need to
    # be handled using myBaseReader's process_metadata() function.
    # myBaseReader = BaseReader(settings)
    # myMarkdownReader = MarkdownReader(settings)
    myMarkdownReader = MDITReader(settings)
    myBaseReader = myMarkdownReader

    file_extensions = [
        # "txt",
    ] + myMarkdownReader.file_extensions

    for post_filename in self.get_files(
        paths=settings["TASKNOTES_FOLDER"],
        extensions=file_extensions,
        # exclude=settings["TASKNOTES_EXCLUDES"]
    ):
        post_full_filename = settings["PATH"] + os.sep + post_filename

        # # TODO: Check for cached version
        # article = articleGenerator.get_cached_data(post, None)
        # if article is None:

        # content, metadata = myMarkdownReader.read(source_path=post)
        content, metadata = myMarkdownReader.read(source_path=post_full_filename)

        new_article_metadata = {
            "category": myBaseReader.process_metadata(
                "category",
                settings.get("TASKNOTES_CATEGORY", DEFAULT_TASKNOTES_CATEGORY),
            ),
            # "tags": myBaseReader.process_metadata("tags", "tagA, tagB"),
            "tasknote": myBaseReader.process_metadata("tasknote", True),
        }

        post_slug = settings["TASKNOTES_SLUG"].format(**metadata)
        metadata["slug"] = post_slug

        try:
            new_article_metadata["author"] = myBaseReader.process_metadata(
                "author", settings["AUTHOR"]
            )
        except KeyError:
            # if author isn't set by either the general settings or the
            # TaskNote metadata, we don't need to force one
            pass

        new_article_metadata["title"] = metadata["title"]
        new_article_metadata["date"] = metadata["date"]
        new_article_metadata["slug"] = post_slug
        new_article_metadata["save_as"] = myBaseReader.process_metadata(
            "save_as", settings["TASKNOTES_SAVE_AS"].format(**metadata)
        )
        new_article_metadata["url"] = myBaseReader.process_metadata(
            "url", settings["TASKNOTES_URL"].format(**metadata)
        )

        if "image" in metadata.keys():
            new_article_metadata["image"] = myBaseReader.process_metadata(
                "image", metadata["image"]
            )

        if "tags" in metadata.keys():
            # new_article_metadata["tags"] = myBaseReader.process_metadata("tags", metadata["tags"])
            new_article_metadata["tags"] = metadata["tags"]

        if "task_status" in metadata.keys():
            new_article_metadata["task_status"] = metadata["task_status"]
        elif "status" in metadata.keys():
            new_article_metadata["task_status"] = metadata["task_status"]

        if "threshold_date" in metadata.keys():
            new_article_metadata["threshold"] = metadata["threshold_date"]
        elif "threshold" in metadata.keys():
            new_article_metadata["threshold"] = metadata["threshold"]

        # metadata keys that go straight across do not need to be listed
        # if "priority" in metadata.keys():
        #     new_article_metadata["priority"] = metadata["priority"]
        # if "completed" in metadata.keys():
        #     new_article_metadata["completed"] = metadata["completed"]
        # # TODO: This should be a list
        # if "contexts" in metadata.keys():
        #     new_article_metadata["contexts"] = metadata["contexts"]
        # # TODO: This should be a list
        # if "projects" in metadata.keys():
        #     new_article_metadata["projects"] = metadata["projects"]
        # if "recurrance" in metadata.keys():
        #     new_article_metadata["recurrance"] = metadata["recurrance"]
        # if "scheduled" in metadata.keys():
        #     new_article_metadata["scheduled"] = metadata["scheduled"]
        # if "due" in metadata.keys():
        #     new_article_metadata["due"] = metadata["due"]
        # if "cancelled" in metadata.keys():
        #     new_article_metadata["cancelled"] = metadata["cancelled"]
        # if "completed" in metadata.keys():
        #     new_article_metadata["completed"] = metadata["completed"]
        # # TODO: derive this from the timename??
        # if "task_id" in metadata.keys():
        #     new_article_metadata["task_id"] = metadata["task_id"]
        # # TODO: this should be a list
        # if "depends_on" in metadata.keys():
        #     new_article_metadata["depends_on"] = metadata["depends_on"]

        # NOTE:
        # new_article_metadata is set by pelicanconf.py
        # metadata is set from the tasknote and is given higher precedence
        # here.
        # Do this before we start trying to read from the metadata to fill out
        # the `todo_title` line
        new_article_metadata.update(metadata)

        # Assemble Tasks-style line
        # this is the presented as the "title" of the todo item, with various
        # metadata directly embedded. Example:
        # - [x] take out the trash #tags 🆔 abcdef ⛔ ghijkl 🔺/⏫/🔼/ /🔽/⏬️
        #   🔁 every Sunday ➕ 2021-04-09 🛫 2021-04-09 ⏳ 2021-04-09
        #   📅 2021-04-09 ❌ 2021-04-09 ✅ 2021-04-09 ⏰ YYYY-MM-DD HH:mm
        todo_title = ""

        # this is the todo item, as would be read in the todo.txt format
        todotxt_line = ""

        _data_task = " "
        # These checkboxes match the formatting from my Fancy-Checkboxes plugin
        # for Markdown-IT. They will need to be styled by the theme in use.
        # TODO: allow these lists to be plugin settings
        if "task_status" not in new_article_metadata:
            pass
        elif (
            new_article_metadata["task_status"].lower()
            in settings["TASKNOTES_IN_PROGRESS_STATUS"]
        ):
            _data_task = "/"
        elif (
            new_article_metadata["task_status"].lower()
            in settings["TASKNOTES_CANCELLED_STATUS"]
        ):
            _data_task = "-"
            todotxt_line += "- "  # TODO: is this the right way to show this??
        elif (
            new_article_metadata["task_status"].lower()
            in settings["TASKNOTES_DONE_STATUS"]
        ):
            _data_task = "x"
            todotxt_line += "x "
        elif (
            new_article_metadata["task_status"].lower()
            in settings["TASKNOTES_DUPLICATE_STATUS"]
        ):
            _data_task = "-"
            todotxt_line += "- "
        else:
            # _data_task = " "
            pass

        _todo_checkbox = ""
        _todo_checkbox += '<input class="task-list-item-checkbox" '
        _todo_checkbox += 'disabled="disabled" type="checkbox" data-task="'
        _todo_checkbox += _data_task
        _todo_checkbox += '" /><span data-task="'
        _todo_checkbox += _data_task
        _todo_checkbox += '"></span>'

        new_article_metadata["tasknote_checkbox"] = _todo_checkbox
        todo_title += _todo_checkbox

        # priorities are removed from completed items, so they sort to the bottom
        if (
            "priority" in new_article_metadata
            and "completed" not in new_article_metadata
        ):
            todotxt_line += "(" + new_article_metadata["priority"].upper()[:1] + ") "

        if (
            "completed" in new_article_metadata
            and new_article_metadata["completed"]
            and new_article_metadata["date"]
        ):
            todotxt_line += new_article_metadata["completed"].strftime("%Y-%m-%d") + " "

        if new_article_metadata["date"]:
            todotxt_line += new_article_metadata["date"].strftime("%Y-%m-%d") + " "

        todo_title += " " + new_article_metadata["title"]
        todotxt_line += new_article_metadata["title"] + " "

        # TODO: Render as a link (a project should have a rendered page (or post))
        # TODO: Process Wikilinks here
        if "projects" in new_article_metadata:
            if isinstance(new_article_metadata["projects"], list):
                todo_title += " " + " ".join(
                    [
                        "+" + x
                        for x in new_article_metadata["projects"]
                        if x not in ["null", None]
                    ]
                )
                todotxt_line += (
                    " ".join(
                        [
                            "+" + x
                            for x in new_article_metadata["projects"]
                            if x not in ["null", None]
                        ]
                    )
                    + " "
                )
            elif isinstance(
                new_article_metadata["projects"], str
            ) and new_article_metadata["projects"] not in ["null", None]:
                todo_title += " +" + new_article_metadata["projects"]
                todotxt_line += new_article_metadata["projects"] + " "

        if "tags" in new_article_metadata.keys():
            # metadata["tags"] is already a list of `pelican.urlwrappers.Tag`
            for tag in new_article_metadata["tags"]:
                tag_url = settings["SITEURL"] + "/" + tag.url
                tag_link = f'<a href="{tag_url}" class="tasknotes-tag">#{tag.name}</a>'
                todo_title += " " + tag_link
        todotxt_line += (
            " ".join(["#" + tag.name for tag in new_article_metadata["tags"]]) + " "
        )

        if "contexts" in new_article_metadata:
            if isinstance(new_article_metadata["contexts"], list):
                try:
                    todo_title += " " + " ".join(
                        [
                            "@" + x
                            for x in new_article_metadata["contexts"]
                            if x not in ["null", None]
                        ]
                    )
                    todotxt_line += (
                        " ".join(
                            [
                                "@" + x
                                for x in new_article_metadata["contexts"]
                                if x not in ["null", None]
                            ]
                        )
                        + " "
                    )
                except TypeError as e:
                    print(
                        f'{todo_title=} {todotxt_line=} {new_article_metadata["contexts"]=}'
                    )
                    raise e
            elif isinstance(
                new_article_metadata["contexts"], str
            ) and new_article_metadata["contexts"] not in ["null", None]:
                todo_title += " " + " @" + new_article_metadata["contexts"]
                todotxt_line += " @" + new_article_metadata["contexts"] + " "

        if "priority" not in new_article_metadata:
            pass
        elif new_article_metadata["priority"].lower() in ["a"]:
            todo_title += ' <span title="Highest Priority">🔺</span>'
        elif new_article_metadata["priority"].lower() in ["b", "high"]:
            todo_title += ' <span title="High Priority">⏫</span>'
        elif new_article_metadata["priority"].lower() in ["c", "d", "n"]:
            todo_title += ' <span title="Medium Priority">🔼</span>'
        elif new_article_metadata["priority"].lower() in ["low", "v", "w"]:
            todo_title += ' <span title="Low Priority">🔽</span>'
        elif new_article_metadata["priority"].lower() in ["z", "someday"]:
            todo_title += ' <span title="Lowest Priority">⏬️</span>'

        if "recurrence" in new_article_metadata:
            todo_title += (
                ' <span title="Recurrence">🔁</span>'
                + new_article_metadata["recurrence"]
            )
            todotxt_line += "rrule:" + new_article_metadata["recurrence"] + " "

        if new_article_metadata["date"]:
            todo_title += (
                ' <span title="Created Date">➕</span><time datetime="'
                + new_article_metadata["date"].isoformat()
                + '">'
                + new_article_metadata["date"].strftime("%Y-%m-%d")
                + "</time>"
            )

        if "threshold" in new_article_metadata:
            todo_title += (
                ' <span title="Threshold (Start) Date">🛫</span><time datetime="'
                + new_article_metadata["threshold"].isoformat()
                + '">'
                + new_article_metadata["threshold"].strftime("%Y-%m-%d")
                + "</time>"
            )
            todotxt_line += (
                "t:" + new_article_metadata["threshold"].strftime("%Y-%m-%d") + " "
            )

        if "scheduled" in new_article_metadata:
            todo_title += (
                ' <span title="Scheduled Date">⏳</span><time datetime="'
                + new_article_metadata["scheduled"].isoformat()
                + '">'
                + new_article_metadata["scheduled"].strftime("%Y-%m-%d")
                + "</time>"
            )

        if "due" in new_article_metadata:
            todo_title += (
                ' <span title="Due Date">📅</span><time datetime="'
                + new_article_metadata["due"].isoformat()
                + '">'
                + new_article_metadata["due"].strftime("%Y-%m-%d")
                + "</time>"
            )
            todotxt_line += (
                "due:" + new_article_metadata["due"].strftime("%Y-%m-%d") + " "
            )

        # Canceled tasks don't have a "canceled date", but are given a
        # `(task_)status` of `canceled` and marked `completed` on the date they
        # are canceled.
        # TODO: separate cancelled and duplicated tasks
        if (
            "task_status" in new_article_metadata
            and (
                new_article_metadata["task_status"].lower()
                in settings["TASKNOTES_CANCELLED_STATUS"]
                or new_article_metadata["task_status"].lower()
                in settings["TASKNOTES_DUPLICATE_STATUS"]
            )
            and "completed" in new_article_metadata
        ):
            todo_title += (
                ' <span title="Date Cancelled">❌</span><time datetime="'
                + new_article_metadata["completed"].isoformat()
                + '">'
                + new_article_metadata["completed"].strftime("%Y-%m-%d")
                + "</time>"
            )
        # Tasks are assumed to be both "Completed" (successfully) and "Canceled"
        elif "completed" in new_article_metadata:
            todo_title += (
                ' <span title="Date Completed">✅</span><time datetime="'
                + new_article_metadata["completed"].isoformat()
                + '">'
                + new_article_metadata["completed"].strftime("%Y-%m-%d")
                + "</time>"
            )

        if "task_id" in new_article_metadata:
            todo_title += (
                ' <span title="Task ID">🆔</span>' + new_article_metadata["task_id"]
            )
            todotxt_line += "id:" + new_article_metadata["task_id"] + " "

        # TODO: render these as links to the other to-do items
        if "depends_on" in new_article_metadata:
            todo_title += ' <span title="Depends On">⛔</span>' + ",".join(
                new_article_metadata["depends_on"]
            )
            # 'p:' for "parent"
            todotxt_line += "p:" + ",".join(new_article_metadata["depends_on"]) + " "

        # move trailing space, if any
        todotxt_line = todotxt_line.rstrip()

        # run through Markdown rendered (to fix links)
        md = myMarkdownReader.get_processor()
        todo_title = md.render(todo_title)
        todo_title = myMarkdownReader.drop_frame_html_tags(todo_title, p=True)

        new_article_metadata["summary"] = todo_title

        # overrides "context" key shared to Jinja template processing
        try:
            del new_article_metadata["context"]
        except KeyError:
            pass

        new_article = Article(
            content or "",
            new_article_metadata,
            settings=self.settings,
            context=self.context,
        )

        # `source_path` is needed as an attribute, rather than part of the
        # metadata
        new_article.source_path = metadata["source_path"] = post_filename

        # # Cache generated file
        # articleGenerator.cache_data(f, article)

        # these should be run by the generator, rather than here
        # to solve issue of Jinja breaking due to KeyError "generated_content"
        # Ensure generated_content exists in context
        if "generated_content" not in self.context:
            self.context["generated_content"] = {}
        self.add_source_path(new_article)
        self.add_static_links(new_article)

        self.articles.insert(0, new_article)
        logger.debug("%s %s", LOG_PREFIX, todotxt_line)
        _todotxt_lines.append(todotxt_line)
        _tasknote_count += 1

    # apply sorting
    logger.debug(
        '%s sorting order: "%s"',
        LOG_PREFIX,
        settings.get("ARTICLE_ORDER_BY", "reversed-date"),
    )
    self.articles = order_content(
        self.articles, settings.get("ARTICLE_ORDER_BY", "reversed-date")
    )


def pelican_finalized(pelican: Pelican) -> None:
    global _tasknote_count
    print(
        "%s Processed %s tasknote%s."
        % (LOG_PREFIX, _tasknote_count, "s" if _tasknote_count != 1 else "")
    )

import logging

from minchin.pelican.readers.commonmark.reader import clean_dates

from .constants import (
    DEFAULT_CANCELLED_STATUS,
    DEFAULT_DONE_STATUS,
    DEFAULT_DUPLICATE_STATUS,
    DEFAULT_IN_PROGRESS_STATUS,
    LOG_PREFIX,
    __url__,
    __version__,
)

logger = logging.getLogger(__name__)


def check_settings(pelican):
    """
    Insert defaults in Pelican settings, as needed.
    """
    logger.debug("%s massaging settings, setting defaults." % LOG_PREFIX)

    if "TASKNOTES_FOLDER" not in pelican.settings.keys():
        pelican.settings["TASKNOTES_FOLDER"] = "tasks"
        logger.debug(
            '%s TASKNOTES_FOLDER set to "%s"',
            LOG_PREFIX,
            pelican.settings["TASKNOTES_FOLDER"],
        )
    else:
        logger.debug(
            '%s TASKNOTES_FOLDER previously set manually. Is "%s"',
            LOG_PREFIX,
            pelican.settings["TASKNOTES_FOLDER"],
        )

    if "TASKNOTES_SAVE_AS" not in pelican.settings.keys():
        pelican.settings["TASKNOTES_SAVE_AS"] = pelican.settings["ARTICLE_SAVE_AS"]
        logger.debug(
            '%s TASKNOTES_SAVE_AS set to "%s"',
            LOG_PREFIX,
            pelican.settings["TASKNOTES_SAVE_AS"],
        )
    else:
        logger.debug(
            '%s TASKNOTES_SAVE_AS previously set manually. Is "%s"',
            LOG_PREFIX,
            pelican.settings["TASKNOTES_SAVE_AS"],
        )

    if "TASKNOTES_SLUG" not in pelican.settings.keys():
        pelican.settings["TASKNOTES_SLUG"] = "task-{date:%Y%m%d%H%M}"
        logger.debug(
            '%s TASKNOTES_SLUG set to "%s"',
            LOG_PREFIX,
            pelican.settings["TASKNOTES_SLUG"],
        )
    else:
        logger.debug(
            '%s TASKNOTES_SLUG previously set manually. Is "%s"',
            LOG_PREFIX,
            pelican.settings["TASKNOTES_SLUG"],
        )

    if "TASKNOTES_URL" not in pelican.settings.keys():
        pelican.settings["TASKNOTES_URL"] = pelican.settings["ARTICLE_URL"]
        logger.debug(
            '%s TASKNOTES_URL set to "%s"',
            LOG_PREFIX,
            pelican.settings["TASKNOTES_URL"],
        )
    else:
        logger.debug(
            '%s TASKNOTES_URL previously set manually. Is "%s"',
            LOG_PREFIX,
            pelican.settings["TASKNOTES_URL"],
        )

    if "TASKNOTES_IN_PROGRESS_STATUS" not in pelican.settings.keys():
        pelican.settings["TASKNOTES_IN_PROGRESS_STATUS"] = DEFAULT_IN_PROGRESS_STATUS
        logger.debug(
            "%s TASKNOTES_IN_PROGRESS_STATUS set to default",
            LOG_PREFIX,
        )
    else:
        logger.debug(
            "%s TASKNOTES_IN_PROGRESS_STATUS previously set manually.",
            LOG_PREFIX,
        )

    if "TASKNOTES_CANCELLED_STATUS" not in pelican.settings.keys():
        pelican.settings["TASKNOTES_CANCELLED_STATUS"] = DEFAULT_CANCELLED_STATUS
        logger.debug(
            "%s TASKNOTES_CANCELLED_STATUS set to default",
            LOG_PREFIX,
        )
    else:
        logger.debug(
            "%s TASKNOTES_CANCELLED_STATUS previously set manually.",
            LOG_PREFIX,
        )

    if "TASKNOTES_DUPLICATE_STATUS" not in pelican.settings.keys():
        pelican.settings["TASKNOTES_DUPLICATE_STATUS"] = DEFAULT_DUPLICATE_STATUS
        logger.debug(
            "%s TASKNOTES_DUPLICATE_STATUS set to default",
            LOG_PREFIX,
        )
    else:
        logger.debug(
            "%s TASKNOTES_DUPLICATE_STATUS previously set manually.",
            LOG_PREFIX,
        )

    if "TASKNOTES_DONE_STATUS" not in pelican.settings.keys():
        pelican.settings["TASKNOTES_DONE_STATUS"] = DEFAULT_DONE_STATUS
        logger.debug(
            "%s TASKNOTES_DONE_STATUS set to default",
            LOG_PREFIX,
        )
    else:
        logger.debug(
            "%s TASKNOTES_DONE_STATUS previously set manually.",
            LOG_PREFIX,
        )

    pelican.settings["ARTICLE_EXCLUDES"] += [
        pelican.settings["TASKNOTES_FOLDER"],
    ]
    logger.debug(
        '%s ARTICLE_EXCLUDES updated to "%s"',
        LOG_PREFIX,
        pelican.settings["ARTICLE_EXCLUDES"],
    )

    # # add custom date cleaner
    # # TODO: confirm these are loaded by the CommonMark reader...
    # pelican.settings["METADATA_PROCESSORS_MDIT"]["threshold"] = clean_dates
    # pelican.settings["METADATA_PROCESSORS_MDIT"]["threshold_date"] = clean_dates
    # pelican.settings["METADATA_PROCESSORS_MDIT"]["scheduled"] = clean_dates
    # pelican.settings["METADATA_PROCESSORS_MDIT"]["due"] = clean_dates
    # pelican.settings["METADATA_PROCESSORS_MDIT"]["cancelled"] = clean_dates
    # pelican.settings["METADATA_PROCESSORS_MDIT"]["completed"] = clean_dates


def tasknotes_version(pelican):
    """
    Insert tasknotes version into Pelican context.

    These are indented to be used by the Pelican theme to provide plugin
    details and to link back to the plugin.
    """

    if "TASKNOTES_VERSION" not in pelican.settings.keys():
        pelican.settings["TASKNOTES_VERSION"] = __version__
        logger.debug(
            '%s Adding Tasknotes version "%s" to context.'
            % (LOG_PREFIX, pelican.settings["TASKNOTES_VERSION"])
        )
    else:
        logger.debug(
            '%s TASKNOTES_VERSION already defined. Is "%s".'
            % (LOG_PREFIX, pelican.settings["TASKNOTES_VERSION"])
        )

    if "TASKNOTES_DEV_URL" not in pelican.settings.keys():
        pelican.settings["TASKNOTES_DEV_URL"] = __url__
        logger.debug(
            '%s Adding Tasknotes Dev URL "%s" to context.'
            % (LOG_PREFIX, pelican.settings["TASKNOTES_DEV_URL"])
        )
    else:
        logger.debug(
            '%s TASKNOTES_DEV_URL already defined. Is "%s".'
            % (LOG_PREFIX, pelican.settings["TASKNOTES_DEV_URL"])
        )
        
def register():
    """Register the plugin pieces with Pelican."""
    signals.initialized.connect(check_settings)
    signals.initialized.connect(tasknotes_version)
    signals.article_generator_pretaxonomy.connect(addTaskNoteArticles)
    signals.finalized.connect(pelican_finalized)


# TODO: write todo.txt file; may need to extend "Everything" Writer
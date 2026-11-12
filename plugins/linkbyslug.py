import logging
import re
from pelican import signals

logger = logging.getLogger(__name__)


def replace_slug_links(generators):
    slug_map = {}

    # 1. Collect all generated URLs mapped by slug
    for generator in generators:
        siteurl = generator.settings.get('SITEURL', '').rstrip('/')
        for attr in (
            'articles',
            'drafts',
            'hidden_articles',
            'pages',
            'hidden_pages',
        ):
            for item in getattr(generator, attr, []):
                if hasattr(item, 'slug') and hasattr(item, 'url'):
                    url = item.url.lstrip('/')
                    slug_map[item.slug] = f'{siteurl}/{url}'

    # 2. Match {slug}my-slug with an optional #anchor fragment
    # Handles both raw {slug} and Docutils-encoded %7Bslug%7D
    pattern = re.compile(
        r'(?:\{slug\}|%7Bslug%7D)([a-zA-Z0-9_-]+)(#[a-zA-Z0-9_.:-]+)?'
    )

    def _replacer(match):
        slug = match.group(1)
        fragment = match.group(2) or ''
        if slug in slug_map:
            return f'{slug_map[slug]}{fragment}'
        logger.warning('link_by_slug: Could not resolve slug "%s"', slug)
        return match.group(0)

    # 3. Replace occurrences in rendered content and cached summaries
    for generator in generators:
        for attr in (
            'articles',
            'drafts',
            'hidden_articles',
            'pages',
            'hidden_pages',
        ):
            for item in getattr(generator, attr, []):
                if getattr(item, '_content', None):
                    item._content = pattern.sub(_replacer, item._content)
                if getattr(item, '_summary', None):
                    item._summary = pattern.sub(_replacer, item._summary)


def register():
    signals.all_generators_finalized.connect(replace_slug_links)

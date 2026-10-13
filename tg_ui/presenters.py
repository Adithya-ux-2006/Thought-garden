"""Turns a note into the plain data the shared note macros render.

Works with either app's Note model (both have id/title/content/category/
tags/created_at/updated_at/is_pinned/is_archived) and never touches the
database: growth stage and connection count are passed in by the caller,
which already has them.
"""

import math
import re
from datetime import datetime, timezone

from tg_ui import categories, flowers

WORDS_PER_MINUTE = 200
PLAIN_LIMIT = 900

_FENCE = re.compile(r'```.*?```', re.S)
_IMAGE = re.compile(r'!\[([^\]]*)\]\([^)]*\)')
_LINK = re.compile(r'\[([^\]]+)\]\([^)]*\)')
_HTML = re.compile(r'<[^>]+>')
_LINE_MARKS = re.compile(r'^\s{0,3}(?:#{1,6}\s+|>\s?|[-*+]\s+|\d+[.)]\s+)', re.M)
_EMPHASIS = re.compile(r'(\*\*|__|\*|_|~~|`)')
_SPACE = re.compile(r'\s+')


def plain_text(markdown, limit=PLAIN_LIMIT):
    """Readable text from Markdown, for previews: no syntax, one line."""
    text = markdown or ''
    text = _FENCE.sub(' ', text)
    text = _IMAGE.sub(r'\1', text)
    text = _LINK.sub(r'\1', text)
    text = _HTML.sub(' ', text)
    text = _LINE_MARKS.sub('', text)
    text = _EMPHASIS.sub('', text)
    text = _SPACE.sub(' ', text).strip()
    if len(text) > limit:
        text = text[:limit].rsplit(' ', 1)[0] + '…'
    return text


def word_count(markdown):
    return len(plain_text(markdown, limit=10 ** 9).split())


def reading_minutes(markdown):
    return max(1, math.ceil(word_count(markdown) / WORDS_PER_MINUTE))


def display_tags(tag_names, category):
    """Tag names minus one equal to the note's category (it would repeat
    the category badge sitting right next to it)."""
    if not category:
        return list(tag_names)
    folded = category.strip().casefold()
    return [t for t in tag_names if t.strip().casefold() != folded]


def _date_label(value, with_year=True):
    if not value:
        return ''
    fmt = '%b %d, %Y' if with_year else '%b %d'
    return value.strftime(fmt).replace(' 0', ' ')


def _is_this_year(value):
    return bool(value) and value.year == datetime.now(timezone.utc).year


def note_view(note, stage=None, connections=None):
    """A dict describing `note` for the tg/notes.html macros."""
    tag_names = [t.name for t in (note.tags or [])]
    category = note.category or None
    stage = stage if stage in flowers.STAGES else None
    flower = categories.flower(category)
    created = note.created_at
    updated = note.updated_at
    return {
        'id': note.id,
        'title': note.title,
        'plain': plain_text(note.content),
        'words': word_count(note.content),
        'minutes': reading_minutes(note.content),
        'category': category,
        'category_label': categories.display_name(category),
        'category_class': categories.badge_class(category),
        'hue_class': f'tg-hue-{categories.slug(category)}',
        'is_wild': categories.is_wild(category),
        'flower': flower,
        'flower_name': flowers.flower_name(flower),
        'stage': stage,
        'stage_label': flowers.STAGE_LABELS.get(stage, ''),
        # A note shown without a known stage still gets its flower in bloom.
        'plant': flowers.plant_filename(category, stage or 'tree'),
        'tags': tag_names,
        'shown_tags': display_tags(tag_names, category),
        'created_at': created,
        'updated_at': updated,
        'created_label': _date_label(created),
        'created_short': _date_label(created, with_year=not _is_this_year(created)),
        'updated_label': _date_label(updated),
        'was_edited': bool(created and updated and (updated - created).total_seconds() > 60),
        'is_pinned': bool(note.is_pinned),
        'is_archived': bool(note.is_archived),
        'connections': connections,
    }


def flower_key(category_values):
    """Legend rows for the categories present in a garden: one row per
    flower, so aliases ('Ideas' and 'Creativity') share a line."""
    rows, seen = [], set()
    for value in category_values:
        flower = categories.flower(value)
        if flower in seen:
            continue
        seen.add(flower)
        rows.append({
            'label': categories.display_name(value),
            'flower': flower,
            'flower_name': flowers.flower_name(flower),
            'plant': flowers.plant_filename(value, 'tree'),
            'hue_class': f'tg-hue-{categories.slug(value)}',
        })
    return rows

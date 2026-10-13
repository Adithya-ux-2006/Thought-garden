"""Flask-facing helpers over the shared category palette in
tg_ui/categories.py (the single source of truth: stored value, labels,
CSS slug, flower and colours - CSS is generated from it by tg_ui/build.py).

Categories are free text with presets, not an enum (see C9 in FIX_PLAN.md):
anything outside the list still renders, with the wildflower and the
neutral palette.
"""

from tg_ui import categories as _palette

CATEGORIES = _palette.CATEGORIES
DEFAULT_COLOR = _palette.DEFAULT_COLOR

# Convenience preset in the note form with no colour or flower of its own.
EXTRA_FORM_PRESETS = [
    ('Other', 'Other'),
]


def note_form_choices():
    """Choices for NoteForm.category. Not exhaustive by design - the form
    field itself must not reject a value outside this list. The category
    picker (main.js) groups these using the metadata in GARDEN_CATEGORIES."""
    return [('', 'Choose a category')] + [(c['value'], c['label']) for c in CATEGORIES] + EXTRA_FORM_PRESETS


def category_color(category):
    """{background, border} for a category, for server-rendered garden data."""
    return _palette.color(category)


def category_badge_class(category):
    return _palette.badge_class(category)


def garden_category_metadata(extra_values=()):
    """Everything the front-end JS/templates need per category, so main.js
    and the garden templates derive their category list/order/badge class
    from this instead of a second hand-typed copy."""
    return _palette.metadata(extra_values)

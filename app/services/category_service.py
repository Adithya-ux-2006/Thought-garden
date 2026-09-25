"""Single source of truth for the five branded note categories: the value
stored on Note.category, the form label, the CSS badge-class slug, and the
light-mode {background, border} colors used server-side (garden nodes,
category legend). Dark-mode values live separately in
app/static/css/style.css's --category-* tokens (keyed by the same slug) -
CSS can't be generated from here since Flask never knows which theme the
browser is in.

Previously hand-mirrored in four places (forms.py's SelectField choices,
garden/routes.py's get_category_color(), main.js's category constants, and
garden/index.html's hardcoded filter legend), which had drifted: 'AI' and
'Artificial Intelligence' both existed as separate color-map keys even
though only 'AI' is ever stored (the label was mistaken for a second
value), and any category outside the five had no color mapping at all.
"""

CATEGORIES = [
    {'value': 'AI', 'label': 'Artificial Intelligence', 'short_label': 'AI', 'slug': 'ai',
     'background': '#a99bea', 'border': '#5c5580'},
    {'value': 'Cybersecurity', 'label': 'Cybersecurity', 'short_label': 'Cyber', 'slug': 'cyber',
     'background': '#e58b78', 'border': '#7d4c42'},
    {'value': 'Software Engineering', 'label': 'Software Engineering', 'short_label': 'SE', 'slug': 'se',
     'background': '#6faf8f', 'border': '#3d604e'},
    {'value': 'Operating Systems', 'label': 'Operating Systems', 'short_label': 'OS', 'slug': 'os',
     'background': '#d9a441', 'border': '#775a23'},
    {'value': 'Research', 'label': 'Research', 'short_label': 'Research', 'slug': 'research',
     'background': '#6f9db5', 'border': '#3d5663'},
]

# Convenience presets in the note form with no brand color/slug of their own
# - they fall back to DEFAULT_COLOR, same as any other free-typed category.
EXTRA_FORM_PRESETS = [
    ('Ideas', 'Ideas'),
    ('Study', 'Study Material'),
    ('Other', 'Other'),
]

DEFAULT_COLOR = {'background': '#d99a68', 'border': '#775439'}

_BY_VALUE = {c['value']: c for c in CATEGORIES}


def note_form_choices():
    """Choices for NoteForm.category. Not exhaustive by design - the form
    field itself must not reject a value outside this list (see C9 in
    FIX_PLAN.md: categories are free text with presets, not a real enum)."""
    return [('', 'Select Category')] + [(c['value'], c['label']) for c in CATEGORIES] + EXTRA_FORM_PRESETS


def category_color(category):
    """{background, border} for a category, for server-rendered garden data."""
    c = _BY_VALUE.get(category)
    return {'background': c['background'], 'border': c['border']} if c else dict(DEFAULT_COLOR)


def category_badge_class(category):
    c = _BY_VALUE.get(category)
    return f"badge-category-{c['slug']}" if c else 'badge-category-none'


def garden_category_metadata():
    """Everything the garden's front-end JS/templates need per category,
    so main.js and garden/index.html derive their category list/order/
    badge-class from this instead of a second hand-typed copy."""
    return [
        {'value': c['value'], 'label': c['label'], 'short_label': c['short_label'], 'slug': c['slug']}
        for c in CATEGORIES
    ]

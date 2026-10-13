"""The category palette: every branded category's stored value, labels,
CSS slug, flower and colours, plus how free-typed categories resolve.

Categories stay free text (Note.category is a plain string) - this list is
the set of presets that get their own colour and flower. Anything else,
including a missing category, resolves to the wildflower and the neutral
"none" palette, so a new custom category always renders gracefully.

Colours:
- background/border: the garden node fill and ring (light canvas values,
  the same ones the server has always sent for graph nodes);
- light/dark `soft_bg`/`soft_text`: badge surfaces, each pair >= 4.5:1
  (tests/test_tg_ui.py checks the contrast);
- dark `hue`: the dot/ring hue on dark surfaces.
`build.py` turns this list into static/css/categories.css, so CSS never
needs a second hand-typed copy.
"""

GROUP_CREATIVE = 'Creative & personal'
GROUP_KNOWLEDGE = 'Knowledge & work'

CATEGORIES = [
    # ---- creative & personal ----
    {'value': 'Writing', 'label': 'Writing', 'short_label': 'Writing', 'slug': 'writing',
     'group': GROUP_CREATIVE, 'flower': 'rose',
     'background': '#d9798f', 'border': '#7b3b4b',
     'light': {'soft_bg': '#F8E6EA', 'soft_text': '#7A3446'},
     'dark': {'hue': '#e693a6', 'soft_bg': '#43262D', 'soft_text': '#F2B5C3'}},
    {'value': 'Creativity', 'label': 'Creativity & ideas', 'short_label': 'Creativity', 'slug': 'creativity',
     'group': GROUP_CREATIVE, 'flower': 'daisy',
     'background': '#a9c35a', 'border': '#56662a',
     'light': {'soft_bg': '#EEF3DD', 'soft_text': '#4A5820'},
     'dark': {'hue': '#b8cf6e', 'soft_bg': '#323A1E', 'soft_text': '#CFE08F'}},
    {'value': 'Personal', 'label': 'Personal reflections', 'short_label': 'Personal', 'slug': 'personal',
     'group': GROUP_CREATIVE, 'flower': 'lotus',
     'background': '#e6a0bd', 'border': '#7e4a60',
     'light': {'soft_bg': '#F8E8EF', 'soft_text': '#74405A'},
     'dark': {'hue': '#eab0c8', 'soft_bg': '#40283A', 'soft_text': '#F2C2D6'}},
    {'value': 'Philosophy', 'label': 'Philosophy', 'short_label': 'Philosophy', 'slug': 'philosophy',
     'group': GROUP_CREATIVE, 'flower': 'lavender',
     'background': '#b07fc0', 'border': '#5e3f69',
     'light': {'soft_bg': '#F1E7F4', 'soft_text': '#5C3C68'},
     'dark': {'hue': '#c398d1', 'soft_bg': '#36283D', 'soft_text': '#DDB9EA'}},
    {'value': 'Design', 'label': 'Design', 'short_label': 'Design', 'slug': 'design',
     'group': GROUP_CREATIVE, 'flower': 'tulip',
     'background': '#ee9a5a', 'border': '#80502a',
     'light': {'soft_bg': '#FBEBDD', 'soft_text': '#7A4720'},
     'dark': {'hue': '#f0aa72', 'soft_bg': '#44301F', 'soft_text': '#F6C59C'}},
    # ---- knowledge & work ----
    {'value': 'Research', 'label': 'Research', 'short_label': 'Research', 'slug': 'research',
     'group': GROUP_KNOWLEDGE, 'flower': 'iris',
     'background': '#6f9db5', 'border': '#3d5663',
     'light': {'soft_bg': '#E4EEF1', 'soft_text': '#334C59'},
     'dark': {'hue': '#80a8bd', 'soft_bg': '#213C40', 'soft_text': '#A9CADB'}},
    # One home for coursework, revision and technical topics; a subject name
    # (Operating Systems, Cybersecurity...) goes on the note as a tag.
    {'value': 'Study', 'label': 'Study', 'short_label': 'Study', 'slug': 'study',
     'group': GROUP_KNOWLEDGE, 'flower': 'bluebell',
     'background': '#5bb5a6', 'border': '#2c6158',
     'light': {'soft_bg': '#DFF2EE', 'soft_text': '#275A51'},
     'dark': {'hue': '#72c4b6', 'soft_bg': '#1B3F3A', 'soft_text': '#9EDCD0'}},
    {'value': 'Business', 'label': 'Business & strategy', 'short_label': 'Business', 'slug': 'business',
     'group': GROUP_KNOWLEDGE, 'flower': 'sunflower',
     'background': '#e9bf3c', 'border': '#75601a',
     'light': {'soft_bg': '#F8F0D2', 'soft_text': '#665112'},
     'dark': {'hue': '#edc95a', 'soft_bg': '#3E3519', 'soft_text': '#F1D683'}},
    {'value': 'AI', 'label': 'Artificial Intelligence', 'short_label': 'AI', 'slug': 'ai',
     'group': GROUP_KNOWLEDGE, 'flower': 'orchid',
     'background': '#a99bea', 'border': '#5c5580',
     'light': {'soft_bg': '#EDEBF8', 'soft_text': '#4E4772'},
     'dark': {'hue': '#b3a7ec', 'soft_bg': '#2F3446', 'soft_text': '#CBC2F4'}},
]

# Free-typed values that mean a branded category. They keep their stored
# text and simply borrow the matching category's colour and flower: older
# notes used 'Ideas' / 'Study Material', and the retired technical presets
# (Software Engineering, Cybersecurity, Operating Systems) now read as Study.
ALIASES = {
    'ideas': 'creativity',
    'idea': 'creativity',
    'study material': 'study',
    'learning': 'study',
    'software engineering': 'study',
    'cybersecurity': 'study',
    'operating systems': 'study',
    'artificial intelligence': 'ai',
    'technology': 'ai',
    'tech': 'ai',
    'journal': 'personal',
    'reflection': 'personal',
    'reflections': 'personal',
    'strategy': 'business',
    'poetry': 'writing',
    'fiction': 'writing',
}

# Garden node fill/ring for anything unbranded (unchanged from before).
DEFAULT_COLOR = {'background': '#d99a68', 'border': '#775439'}
NONE_SLUG = 'none'
WILD_FLOWER = 'wildflower'
# How a missing category reads in the UI. The stored value stays NULL and
# the garden API still sends 'Uncategorized'; this is display only.
WILD_LABEL = 'Wild thoughts'
UNCATEGORIZED = 'Uncategorized'

_BY_VALUE = {c['value']: c for c in CATEGORIES}
_BY_SLUG = {c['slug']: c for c in CATEGORIES}
_BY_FOLDED = {c['value'].casefold(): c for c in CATEGORIES}


def resolve(category):
    """The branded category a stored value means, or None if it has none."""
    if not category:
        return None
    exact = _BY_VALUE.get(category)
    if exact:
        return exact
    folded = category.strip().casefold()
    if folded in _BY_FOLDED:
        return _BY_FOLDED[folded]
    alias = ALIASES.get(folded)
    return _BY_SLUG.get(alias) if alias else None


def is_wild(category):
    return not category or category == UNCATEGORIZED


def display_name(category):
    """What a category is called on screen: its own text, or 'Wild thoughts'."""
    return WILD_LABEL if is_wild(category) else category


def slug(category):
    c = resolve(category)
    return c['slug'] if c else NONE_SLUG


def badge_class(category):
    return f'badge-category-{slug(category)}'


def flower(category):
    c = resolve(category)
    return c['flower'] if c else WILD_FLOWER


def color(category):
    """{background, border} for the garden node of a category."""
    c = resolve(category)
    return {'background': c['background'], 'border': c['border']} if c else dict(DEFAULT_COLOR)


def presets():
    """(value, label, group) for every branded category, in display order."""
    return [(c['value'], c['label'], c['group']) for c in CATEGORIES]


def metadata(extra_values=()):
    """Per-category data the front-end needs (chips, legend, filters), in
    palette order, followed by any extra stored values (custom categories
    in a user's notes) that aren't branded presets."""
    rows = [
        {'value': c['value'], 'label': c['label'], 'short_label': c['short_label'],
         'slug': c['slug'], 'flower': c['flower'], 'group': c['group']}
        for c in CATEGORIES
    ]
    known = {c['value'] for c in CATEGORIES}
    for value in extra_values:
        if not value or value in known:
            continue
        known.add(value)
        rows.append({'value': value, 'label': display_name(value),
                     'short_label': display_name(value), 'slug': slug(value),
                     'flower': flower(value), 'group': None})
    return rows

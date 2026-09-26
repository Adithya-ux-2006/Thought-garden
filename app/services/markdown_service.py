"""Note content -> safe HTML.

Two independent layers: markdown-it runs with raw HTML disabled (so any
`<tag>` in a note is emitted as escaped text) and rejects dangerous link
schemes; nh3 then re-sanitizes the output against a fixed allowlist, so a
future parser option or plugin can't widen what reaches the page.
"""
import nh3
from markdown_it import MarkdownIt
from markupsafe import Markup

# breaks=True keeps single newlines in pre-Markdown plain-text notes visible.
_parser = MarkdownIt('commonmark', {'html': False, 'breaks': True}).enable(['table', 'strikethrough'])

ALLOWED_TAGS = {
    'p', 'br', 'hr', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    'strong', 'em', 's', 'code', 'pre', 'blockquote',
    'ul', 'ol', 'li', 'a', 'img',
    'table', 'thead', 'tbody', 'tr', 'th', 'td',
}
ALLOWED_ATTRIBUTES = {
    'a': {'href', 'title'},
    'img': {'src', 'alt', 'title'},
    'code': {'class'},
    'ol': {'start'},
}
URL_SCHEMES = {'http', 'https', 'mailto'}


def _attribute_filter(tag, attr, value):
    if tag == 'code' and attr == 'class':
        return value if value.startswith('language-') and value.replace('-', '').isalnum() else None
    return value


def sanitize_html(html):
    return nh3.clean(
        html,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        url_schemes=URL_SCHEMES,
        attribute_filter=_attribute_filter,
        link_rel='noopener noreferrer nofollow',
        strip_comments=True,
    )


def render_markdown(text):
    if not text:
        return Markup('')
    return Markup(sanitize_html(_parser.render(text)).strip())

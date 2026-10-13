"""Renders the shared macros outside Flask (the Streamlit port).

Same templates, same autoescaping; images become data: URIs because the
HTML lands in a page that can't reach Flask's /static.
"""

import base64
import functools
import mimetypes
import os

from jinja2 import Environment, FileSystemLoader, select_autoescape

from tg_ui import STATIC_DIR, TEMPLATE_DIR


@functools.lru_cache(maxsize=256)
def asset_data_uri(path):
    """A static asset (path relative to static/) as a data: URI."""
    full = os.path.normpath(os.path.join(STATIC_DIR, path))
    if not full.startswith(os.path.normpath(STATIC_DIR) + os.sep):
        raise ValueError(f'asset outside static/: {path}')
    mime = mimetypes.guess_type(full)[0] or 'application/octet-stream'
    if full.endswith('.svg'):
        mime = 'image/svg+xml'
    elif full.endswith('.webp'):
        mime = 'image/webp'
    with open(full, 'rb') as fh:
        return f'data:{mime};base64,{base64.b64encode(fh.read()).decode()}'


@functools.lru_cache(maxsize=2)
def environment(inline_assets=True):
    """Jinja environment over tg_ui/templates. With inline_assets, images
    become data: URIs (HTML placed straight into a Streamlit page); without,
    asset paths stay relative to static/ (the garden component's page,
    which is served from static/ itself)."""
    env = Environment(
        loader=FileSystemLoader(TEMPLATE_DIR),
        autoescape=select_autoescape(default=True, default_for_string=True),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    env.globals['tg_asset'] = asset_data_uri if inline_assets else (lambda path: path)
    return env


def macro(name, template='tg/notes.html', inline_assets=True):
    """A shared macro as a Python callable returning safe HTML."""
    return getattr(environment(inline_assets).get_template(template).module, name)


def render(name, *args, template='tg/notes.html', **kwargs):
    return str(macro(name, template)(*args, **kwargs))

"""Thought Garden's shared design package.

One source for everything both frontends draw: the web assets (static/),
the note/category/tag macros (templates/tg/), the category palette and
flower mapping, and the note "view model" the macros render. Flask serves
static/ as its static folder; the Streamlit port loads the same CSS through
st.html() and the same garden through a component rooted at static/.

Nothing in this package imports Flask, Streamlit or either app's models, so
both apps can import it without dragging the other one in.
"""

import os

PACKAGE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(PACKAGE_DIR, 'static')
TEMPLATE_DIR = os.path.join(PACKAGE_DIR, 'templates')

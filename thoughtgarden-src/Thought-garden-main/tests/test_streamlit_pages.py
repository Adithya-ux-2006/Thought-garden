"""Runs every Streamlit page headlessly (streamlit.testing AppTest) against a
throwaway database and checks it renders without an exception, including
the shared tg_ui design (streamlit_ui). Skipped when Streamlit isn't
installed (the Flask-only test environment)."""

import os

import pytest

pytest.importorskip("streamlit")
from streamlit.testing.v1 import AppTest  # noqa: E402

PORT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGES = ["1_Dashboard", "2_Notes", "3_Garden", "4_Search", "5_Insights", "6_Profile"]


@pytest.fixture(scope="module")
def seeded(tmp_path_factory):
    db_path = tmp_path_factory.mktemp("st") / "pages.db"
    previous = os.environ.get("DATABASE_URL")
    os.environ["DATABASE_URL"] = f"sqlite:///{db_path.as_posix()}"
    import config
    import streamlit_db
    import streamlit_notes_ops as ops

    # config reads DATABASE_URL at import; earlier tests may have imported it.
    original_uri = config.Config.SQLALCHEMY_DATABASE_URI
    config.Config.SQLALCHEMY_DATABASE_URI = os.environ["DATABASE_URL"]
    streamlit_db.get_flask_app.cache_clear()
    streamlit_db.run_startup_once.cache_clear()
    streamlit_db.run_startup_once()
    user_id = streamlit_db.ensure_local_user()
    ops.create_note(user_id, title="<b>Lighthouse</b> story", content="A girl keeps a **logbook**.",
                    category="Writing", tags="story idea, poetry")
    ops.create_note(user_id, title="Canal walk", content="Herons like question marks.",
                    category="", tags="observation, poetry")
    ops.create_note(user_id, title="Field notes", content="Birdsong at dawn.",
                    category="Nature walks", tags="observation")
    yield user_id
    config.Config.SQLALCHEMY_DATABASE_URI = original_uri
    streamlit_db.get_flask_app.cache_clear()
    streamlit_db.run_startup_once.cache_clear()
    if previous is None:
        os.environ.pop("DATABASE_URL", None)
    else:
        os.environ["DATABASE_URL"] = previous


def _run(page, user_id):
    at = AppTest.from_file(os.path.join(PORT_DIR, "streamlit_pages", f"{page}.py"), default_timeout=60)
    at.session_state["auth_ok"] = True
    at.session_state["user_id"] = user_id
    return at.run()


@pytest.mark.parametrize("page", PAGES)
def test_page_renders_without_exceptions(seeded, page):
    at = _run(page, seeded)
    assert not at.exception, [e.value for e in at.exception]


def test_notes_page_uses_shared_cards_and_escapes_titles(seeded):
    at = _run("2_Notes", seeded)
    html = "".join(el.proto.body for el in at.get("html"))
    assert html.count("<article class=\"tg-note tg-note--editorial") == 3
    assert "&lt;b&gt;Lighthouse&lt;/b&gt;" in html and "<b>Lighthouse" not in html
    assert "data:image/svg+xml;base64," in html  # flowers inlined (no /static in Streamlit)


def test_theme_css_survives_streamlit_sanitizer():
    import streamlit_ui

    css = streamlit_ui._theme_css()
    assert css.startswith("<style>") and "tg-st-hero" in css
    # DOMPurify drops a whole <style> whose text has "<" + word char or "/".
    import re
    assert not re.search(r"<[/\w]", css[len("<style>"):-len("</style>")])

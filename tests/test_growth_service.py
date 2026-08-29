from datetime import datetime, timedelta

from app.services.growth_service import (
    compute_growth_score,
    compute_growth_stage,
    growth_icon_filename,
    was_recently_watered,
)


def test_brand_new_isolated_note_is_a_seed():
    stage = compute_growth_stage(datetime.utcnow(), connection_count=0)
    assert stage == 'seed'


def test_old_well_connected_note_is_a_tree():
    old = datetime.utcnow() - timedelta(days=60)
    stage = compute_growth_stage(old, connection_count=10)
    assert stage == 'tree'


def test_missing_created_at_is_treated_as_a_seed():
    assert compute_growth_stage(None, connection_count=5) == 'seed'


def test_growth_score_is_bounded_between_zero_and_one():
    old = datetime.utcnow() - timedelta(days=999)
    score = compute_growth_score(old, connection_count=999)
    assert 0.0 <= score <= 1.0


def test_growth_icon_filename_has_a_safe_fallback():
    assert growth_icon_filename('not-a-real-stage') == 'seed.svg'
    assert growth_icon_filename('tree') == 'tree.svg'


def test_recently_edited_note_is_watered():
    assert was_recently_watered(datetime.utcnow()) is True


def test_stale_note_is_not_watered():
    old = datetime.utcnow() - timedelta(days=30)
    assert was_recently_watered(old) is False


def test_note_with_no_updated_at_is_not_watered():
    assert was_recently_watered(None) is False

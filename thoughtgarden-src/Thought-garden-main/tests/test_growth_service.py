from datetime import datetime, timedelta

from app.services.growth_service import (
    compute_growth_score,
    compute_growth_stage,
    growth_icon_filename,
)


def test_brand_new_isolated_note_is_a_seed():
    stage = compute_growth_stage(datetime.utcnow(), connection_count=0)
    assert stage == 'seed'


def test_old_well_connected_note_is_a_tree():
    old = datetime.utcnow() - timedelta(days=60)
    stage = compute_growth_stage(old, connection_count=10)
    assert stage == 'tree'


def test_a_week_old_well_connected_note_reaches_tree():
    # Regression test: MAX_AGE_DAYS was originally 30, which made 'tree'
    # unreachable within any normal multi-week usage window (needed 15+
    # days old AND maximally connected, in practice more like a month).
    # A note about a week old with max connections should now clear the
    # 0.75 threshold.
    week_old = datetime.utcnow() - timedelta(days=7)
    assert compute_growth_stage(week_old, connection_count=6) == 'tree'


def test_brand_new_note_cannot_reach_tree_no_matter_how_connected():
    # The "needs both signals" invariant the retuning was careful to keep:
    # connections alone can't fully compensate for age, so a 0-day-old note
    # stays capped well below the tree threshold even with huge fan-out.
    stage = compute_growth_stage(datetime.utcnow(), connection_count=1000)
    assert stage != 'tree'


def test_missing_created_at_is_treated_as_a_seed():
    assert compute_growth_stage(None, connection_count=5) == 'seed'


def test_growth_score_is_bounded_between_zero_and_one():
    old = datetime.utcnow() - timedelta(days=999)
    score = compute_growth_score(old, connection_count=999)
    assert 0.0 <= score <= 1.0


def test_growth_icon_filename_has_a_safe_fallback():
    assert growth_icon_filename('not-a-real-stage') == 'seed.svg'
    assert growth_icon_filename('tree') == 'tree.svg'

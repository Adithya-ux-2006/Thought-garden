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


# ---- zero-connection edge cases ----
# An isolated note (connection_count=0) relies entirely on the age half of
# the score, since the connection half contributes exactly 0 either way.

def test_zero_connections_zero_age_is_a_seed():
    assert compute_growth_stage(datetime.utcnow(), connection_count=0) == 'seed'


def test_zero_connections_note_can_still_reach_sapling_via_age_alone():
    # 14 days old (= MAX_AGE_DAYS), 0 connections: age_score maxes at 1.0,
    # connection_score is 0, score = 0.5*1 + 0.5*0 = 0.5 exactly - a fully
    # isolated note can grow as far as sapling on age alone, but no further
    # (needs some connection to clear 0.75 into tree).
    old = datetime.utcnow() - timedelta(days=14)
    assert compute_growth_score(old, connection_count=0) == 0.5
    assert compute_growth_stage(old, connection_count=0) == 'sapling'


def test_zero_connections_note_never_reaches_tree_no_matter_how_old():
    ancient = datetime.utcnow() - timedelta(days=100000)
    assert compute_growth_stage(ancient, connection_count=0) == 'sapling'


def test_negative_connection_count_is_clamped_not_negative_score():
    # Defensive: connection_count shouldn't be able to go negative in
    # practice, but the clamp (max(0, connection_count)) should mean a
    # negative value behaves identically to zero rather than producing a
    # negative or otherwise out-of-range score.
    assert compute_growth_score(datetime.utcnow(), connection_count=-5) == \
        compute_growth_score(datetime.utcnow(), connection_count=0)


# ---- exact stage-boundary values ----
# compute_growth_stage buckets with strict "<" comparisons (score < 0.25 is
# seed, etc.), so a score that lands EXACTLY on a boundary belongs to the
# stage above it, not below - these pin that down explicitly rather than
# relying on scores that merely happen to fall clearly inside a bucket.

def test_score_exactly_at_seed_sprout_boundary_is_sprout():
    week_old = datetime.utcnow() - timedelta(days=7)
    assert compute_growth_score(week_old, connection_count=0) == 0.25
    assert compute_growth_stage(week_old, connection_count=0) == 'sprout'


def test_score_exactly_at_sprout_sapling_boundary_is_sapling():
    max_connections = datetime.utcnow()
    assert compute_growth_score(max_connections, connection_count=6) == 0.5
    assert compute_growth_stage(max_connections, connection_count=6) == 'sapling'


def test_score_exactly_at_sapling_tree_boundary_is_tree():
    two_weeks_old = datetime.utcnow() - timedelta(days=14)
    assert compute_growth_score(two_weeks_old, connection_count=3) == 0.75
    assert compute_growth_stage(two_weeks_old, connection_count=3) == 'tree'

from datetime import datetime


# Ordered from least to most "grown" - used by the garden UI to pick an icon.
GROWTH_STAGES = ('seed', 'sprout', 'sapling', 'tree')

GROWTH_ICON_FILES = {
    'seed': 'seed.svg',
    'sprout': 'sprout.svg',
    'sapling': 'sapling.svg',
    'tree': 'tree.svg',
}

# Age/connection counts at which the growth score maxes out. Tune these
# once there's real usage data - they're deliberately simple for now.
#
# MAX_AGE_DAYS was originally 30, which made 'tree' (score >= 0.75)
# unreachable in any realistic near-term usage: with the 50/50 weighting
# below, a note needs BOTH signals meaningfully high (neither can fully
# compensate for the other - a brand-new note with 100 connections still
# caps at 0.5, still a sapling), so hitting 0.75 requires age_score alone
# to already be >= 0.5, i.e. half of MAX_AGE_DAYS old. At 30 days that's
# two full weeks minimum, and only if also maximally connected - in
# practice unreachable within a normal multi-week usage window. 14 keeps
# the same "needs both" invariant (0-day-old note still caps at 0.5, never
# tree) but makes it reachable after about a week of real use for a
# well-connected note instead of a month.
MAX_AGE_DAYS = 14
MAX_CONNECTIONS = 6


def compute_growth_score(created_at, connection_count):
    """Combine a note's age and how connected it is into a 0.0-1.0 score.

    Neither signal alone tells the whole story: a brand-new note with
    several connections should grow faster than an old, isolated one.
    This is a pure function (no DB access) so it's easy to test and
    easy to call from any endpoint that already has these two values.
    """
    if not created_at:
        return 0.0

    age_days = (datetime.utcnow() - created_at).days
    age_score = min(1.0, max(0.0, age_days) / MAX_AGE_DAYS)

    connection_score = min(1.0, max(0, connection_count) / MAX_CONNECTIONS)

    return min(1.0, (0.5 * age_score) + (0.5 * connection_score))


def compute_growth_stage(created_at, connection_count):
    """Map a growth score onto one of GROWTH_STAGES."""
    score = compute_growth_score(created_at, connection_count)
    if score < 0.25:
        return 'seed'
    if score < 0.5:
        return 'sprout'
    if score < 0.75:
        return 'sapling'
    return 'tree'


def growth_icon_filename(stage):
    """Look up the static SVG filename for a growth stage, defaulting
    to the seed icon for any unrecognized value."""
    return GROWTH_ICON_FILES.get(stage, GROWTH_ICON_FILES['seed'])

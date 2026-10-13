"""The garden's botanical illustrations: one flower per category, drawn at
each growth stage, generated as small standalone SVGs.

Growth stages keep their stored names and rules (growth_service):
    seed    - a seed resting in soil, with a spark of the category's colour
    sprout  - two seed leaves and a tiny coloured bud
    sapling - a leafy stem carrying a closed bud in the flower's colours
    tree    - the full bloom (shown as "In bloom")
so a young note shows how far it has grown and a mature one shows what it
is. Every plant sits on the same dark-emerald medallion, so it reads as a
garden node on the dark clearing and as a botanical badge on light cards.

`build.py` writes plant_svg() output to static/img/plants/<flower>-<stage>.svg;
nothing renders these at request time.
"""

import math

from tg_ui import categories

STAGES = ('seed', 'sprout', 'sapling', 'tree')
STAGE_LABELS = {'seed': 'Seed', 'sprout': 'Sprout', 'sapling': 'Sapling', 'tree': 'In bloom'}

# species -> (display name, petal light, petal deep). The two petal colours
# also tint the sapling's bud and the seed's spark.
FLOWERS = {
    'rose': ('Rose', '#f7b5c3', '#c94b68'),
    'daisy': ('Daisy', '#fffdf6', '#e9a21d'),
    'lotus': ('Lotus', '#ffe0ec', '#e27aa2'),
    'lavender': ('Lavender', '#d6bdf0', '#7f57b9'),
    'tulip': ('Tulip', '#ffc898', '#e05f27'),
    'iris': ('Iris', '#c2b4f5', '#5a43b8'),
    'bluebell': ('Bluebell', '#b4f0e5', '#3b9a8c'),
    'sunflower': ('Sunflower', '#ffe169', '#ee9a10'),
    'orchid': ('Orchid', '#f8f2ff', '#b49be8'),
    'wildflower': ('Wildflower', '#fde9d9', '#e99a6e'),
}

CX, CY = 32, 31
LEAF = ('#7fd3a0', '#1f6b45')


def flower_name(flower):
    return FLOWERS.get(flower, FLOWERS['wildflower'])[0]


def plant_key(category, stage):
    """'<flower>-<stage>': the file name (minus .svg) for a note's plant."""
    stage = stage if stage in STAGES else 'seed'
    return f'{categories.flower(category)}-{stage}'


def plant_filename(category, stage):
    return f'img/plants/{plant_key(category, stage)}.svg'


# ---------------------------------------------------------------------------
# drawing helpers
# ---------------------------------------------------------------------------

def _n(v):
    s = f'{v:.1f}'
    return s[:-2] if s.endswith('.0') else s


def _lin(gid, light, deep, x2=0, y2=0, x1=0, y1=1):
    return (f'<linearGradient id="{gid}" x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}">'
            f'<stop offset="0" stop-color="{deep}"/><stop offset="1" stop-color="{light}"/></linearGradient>')


def _rad(gid, inner, outer, cx='50%', cy='40%', r='60%'):
    return (f'<radialGradient id="{gid}" cx="{cx}" cy="{cy}" r="{r}">'
            f'<stop offset="0" stop-color="{inner}"/><stop offset="1" stop-color="{outer}"/></radialGradient>')


def _petal(kind, cx, cy, r0, length, width):
    """A petal pointing straight up from (cx, cy - r0)."""
    b = cy - r0
    t = b - length
    w = width
    if kind == 'round':
        return (f'M{_n(cx)} {_n(b)}C{_n(cx - w)} {_n(b - length * .3)} {_n(cx - w * .8)} {_n(t)} {_n(cx)} {_n(t)}'
                f'C{_n(cx + w * .8)} {_n(t)} {_n(cx + w)} {_n(b - length * .3)} {_n(cx)} {_n(b)}Z')
    # pointed
    return (f'M{_n(cx)} {_n(b)}C{_n(cx - w)} {_n(b - length * .35)} {_n(cx - w * .45)} {_n(b - length * .85)} {_n(cx)} {_n(t)}'
            f'C{_n(cx + w * .45)} {_n(b - length * .85)} {_n(cx + w)} {_n(b - length * .35)} {_n(cx)} {_n(b)}Z')


def _ring(kind, n, r0, length, width, fill, offset=0, cx=CX, cy=CY, extra=''):
    out = []
    for i in range(n):
        a = offset + i * 360 / n
        out.append(f'<path d="{_petal(kind, cx, cy, r0, length, width)}" fill="{fill}"'
                   f' transform="rotate({_n(a)} {_n(cx)} {_n(cy)})"{extra}/>')
    return ''.join(out)


def _at(kind, angles, cx, cy, r0, length, width, fill, extra=''):
    return ''.join(
        f'<path d="{_petal(kind, cx, cy, r0, length, width)}" fill="{fill}"'
        f' transform="rotate({_n(a)} {_n(cx)} {_n(cy)})"{extra}/>' for a in angles)


def _dots(n, r, size, fill, cx=CX, cy=CY, offset=0):
    out = []
    for i in range(n):
        a = math.radians(offset + i * 360 / n)
        out.append(f'<circle cx="{_n(cx + r * math.cos(a))}" cy="{_n(cy + r * math.sin(a))}" r="{_n(size)}" fill="{fill}"/>')
    return ''.join(out)


def _leaves(angles=(-128, 128), cx=CX, cy=CY + 4, length=17, width=6.5):
    """Leaves peeking out from behind a bloom, each with a pale midrib."""
    return (_at('pointed', angles, cx, cy, 6, length, width, 'url(#lf)')
            + ''.join(f'<path d="M{_n(cx)} {_n(cy - 7)}L{_n(cx)} {_n(cy - 6 - length * .8)}" stroke="#b9ecd0"'
                      f' stroke-opacity=".45" stroke-width=".7" transform="rotate({_n(a)} {_n(cx)} {_n(cy)})"/>'
                      for a in angles))


def _soil():
    return ('<ellipse cx="32" cy="52" rx="19" ry="7" fill="url(#sl)"/>'
            '<ellipse cx="29" cy="49.5" rx="9" ry="1.6" fill="#8a6a4b" fill-opacity=".35"/>')


# ---------------------------------------------------------------------------
# blooms
# ---------------------------------------------------------------------------

def _rose(light, deep):
    defs = (_lin('p1', light, deep) + _lin('p2', '#ec8aa0', '#a8314f')
            + _rad('pc', '#c4405f', '#7d1f38', cy='45%', r='55%'))
    body = (_leaves()
            + _ring('round', 5, 2, 19, 12, 'url(#p1)')
            + _ring('round', 5, 1, 14, 9, 'url(#p2)', offset=36)
            + _ring('round', 3, 0, 9, 7, 'url(#p2)', offset=15, extra=' fill-opacity=".9"')
            + '<circle cx="32" cy="31" r="4.6" fill="url(#pc)"/>'
            + '<path d="M29.4 31.4c.2-2.4 3.6-3.2 4.8-1.2 1 1.8-.8 3.6-2.5 3-1.2-.4-1.2-1.8-.2-2.1" fill="none"'
              ' stroke="#f6b9c7" stroke-width=".8" stroke-linecap="round"/>'
            + '<path d="M22.5 22c2-2.6 5-4 8-4.2" fill="none" stroke="#fff" stroke-opacity=".35" stroke-width=".9"'
              ' stroke-linecap="round"/>')
    return defs, body


def _daisy(light, deep):
    defs = (_lin('p1', '#ffffff', '#dfe8e2') + _lin('p2', '#f1f5ef', '#c7d4ca')
            + _rad('pc', '#ffe37d', '#e39616', cy='40%', r='60%'))
    body = (_leaves()
            + _ring('round', 18, 4, 17, 3.3, 'url(#p2)', offset=10)
            + _ring('round', 18, 4, 19, 3.6, 'url(#p1)', extra=' stroke="#b9c9bd" stroke-opacity=".35" stroke-width=".4"')
            + '<circle cx="32" cy="31" r="6.6" fill="url(#pc)"/>'
            + _dots(9, 3.6, .55, '#c27a10', offset=20) + _dots(4, 1.6, .5, '#c27a10'))
    return defs, body


def _lotus(light, deep):
    defs = (_lin('p1', '#fff1f6', '#f0a3c2') + _lin('p2', light, deep)
            + _lin('pd', '#5fbf86', '#1c5b3d', x1=0, y1=0, x2=1, y2=1))
    body = ('<ellipse cx="32" cy="50" rx="23" ry="6.5" fill="url(#pd)"/>'
            '<path d="M32 50L50 46" stroke="#0f3d2b" stroke-width=".8" stroke-opacity=".6"/>'
            + _at('pointed', (-52, 0, 52), 32, 45, 0, 25, 8, 'url(#p1)')
            + _at('pointed', (-74, -30, 30, 74), 32, 45, 0, 19, 8, 'url(#p2)')
            + '<ellipse cx="32" cy="36.5" rx="3.6" ry="2.2" fill="#ffd36b"/>'
            + _at('pointed', (0,), 32, 45, 0, 15, 6.5, 'url(#p2)')
            + '<path d="M32 44V33" stroke="#fff" stroke-opacity=".4" stroke-width=".7"/>')
    return defs, body


def _lavender(light, deep):
    defs = _lin('p1', light, deep) + _lin('st', '#8fd3a6', '#2f7a50')
    # (stem path, spike top x/y, spike bottom x, lean in degrees)
    stems = (('M32 57C31 44 31 28 32 9', 32, 9, 31.6, 0), ('M31 57C27 44 24 30 21 15', 21, 15, 24.6, -14),
             ('M33 57C37 44 40 30 43 15', 43, 15, 39.4, 14))
    body = _at('pointed', (-140, 140), 32, 57, 0, 15, 4, 'url(#lf)')
    for d, tx, ty, bx, lean in stems:
        body += f'<path d="{d}" fill="none" stroke="url(#st)" stroke-width="1.3" stroke-linecap="round"/>'
        for k in range(7):
            f = k / 6
            y = ty + f * 24
            x = tx + (bx - tx) * f
            size = 1.4 + f * 1.5
            for side in (-1, 1):
                body += (f'<ellipse cx="{_n(x + side * size * .8)}" cy="{_n(y)}" rx="{_n(size * .75)}" ry="{_n(size * 1.15)}"'
                         f' fill="url(#p1)" transform="rotate({_n(side * 28 + lean)} {_n(x + side * size * .8)} {_n(y)})"/>')
    return defs, body


def _tulip(light, deep):
    defs = _lin('p1', light, deep) + _lin('p2', '#f8a36b', '#b84719') + _lin('st', '#8fd3a6', '#2f7a50')
    body = ('<path d="M32 58C32 50 32 46 32 39" stroke="url(#st)" stroke-width="2.4" stroke-linecap="round"/>'
            '<path d="M32 56C24 50 20 40 21 31C26 38 30 46 32 56Z" fill="url(#lf)"/>'
            '<path d="M32 57C38 52 43 46 44 39C38 43 34 49 32 57Z" fill="url(#lf)" fill-opacity=".85"/>'
            + _at('round', (-20, 20), 32, 41, 0, 22, 8.5, 'url(#p2)')
            + _at('round', (0,), 32, 41, 0, 21, 9.5, 'url(#p1)')
            + '<path d="M30.4 37c-.6-4.4.4-9 2.6-12.4" fill="none" stroke="#fff" stroke-opacity=".45" stroke-width=".9"'
              ' stroke-linecap="round"/>')
    return defs, _scaled(body, 1.14, 32, 36)


def _iris(light, deep):
    defs = (_lin('p1', light, '#6f57c9') + _lin('p2', '#9a84e6', deep)
            + _lin('sg', '#fff3b8', '#f0b52a'))
    body = (_leaves((-150, 150), cy=37, length=18)
            + _at('round', (-150, 150, 180), 32, 31, 1, 19, 9, 'url(#p2)')
            + _at('pointed', (-150, 150, 180), 32, 31, 3, 10, 2.4, 'url(#sg)')
            + _at('round', (-30, 30), 32, 31, 0, 19, 7, 'url(#p1)')
            + _at('round', (0,), 32, 31, 0, 21, 7.5, 'url(#p1)')
            + '<path d="M32 28V13" stroke="#fff" stroke-opacity=".35" stroke-width=".7"/>'
            + '<circle cx="32" cy="31" r="2.6" fill="#4b3399"/>')
    return defs, body


def _orchid(light, deep):
    defs = (_lin('p1', '#fbf7ff', '#c9b4ef') + _lin('p2', light, deep)
            + _lin('lp', '#d65cb2', '#7a1f66'))
    body = (_leaves((-122, 122), cy=38)
            + _at('pointed', (0, 128, 232), 32, 31, 0, 20, 6.4, 'url(#p1)')
            + _at('round', (64, 296), 32, 31, 0, 17, 10.5, 'url(#p2)')
            + _at('round', (180,), 32, 32, 0, 13, 8, 'url(#lp)')
            + _dots(5, 6.5, .65, '#f7d3ea', cx=32, cy=38, offset=200)
            + '<ellipse cx="32" cy="30" rx="2.4" ry="3.2" fill="#fffaf3"/>'
            + '<circle cx="32" cy="28.6" r="1" fill="#f3c25a"/>')
    return defs, body


def _sunflower(light, deep):
    defs = (_lin('p1', light, '#f4ad16') + _lin('p2', '#ffcf3d', deep)
            + _rad('pc', '#7b4a22', '#3a200c', cy='45%', r='55%'))
    body = (_leaves()
            + _ring('pointed', 16, 7, 17, 4.6, 'url(#p2)', offset=11)
            + _ring('pointed', 16, 7, 15, 4.2, 'url(#p1)')
            + '<circle cx="32" cy="31" r="9" fill="url(#pc)"/>'
            + _dots(14, 6.6, .75, '#b77a33') + _dots(9, 4, .7, '#a36a2a', offset=20)
            + _dots(4, 1.6, .6, '#8f5b23', offset=45))
    return defs, body


def _bell(x, y, lean, s, deep):
    """One hanging bell, its top at (x, y), scaled by s."""
    w, h = 4 * s, 10.6 * s
    return (f'<g transform="rotate({lean} {_n(x)} {_n(y)})">'
            f'<path d="M{_n(x - w)} {_n(y)}C{_n(x - w * 1.15)} {_n(y + h * .47)} {_n(x - w * 1.35)} {_n(y + h * .8)} {_n(x - w * 1.8)} {_n(y + h)}'
            f'L{_n(x + w * 1.8)} {_n(y + h)}C{_n(x + w * 1.35)} {_n(y + h * .8)} {_n(x + w * 1.15)} {_n(y + h * .47)} {_n(x + w)} {_n(y)}'
            f'C{_n(x + w * .5)} {_n(y - 3 * s)} {_n(x - w * .5)} {_n(y - 3 * s)} {_n(x - w)} {_n(y)}Z" fill="url(#p1)"/>'
            + ''.join(f'<circle cx="{_n(x + dx * s)}" cy="{_n(y + h + .2)}" r="{_n(1.5 * s)}" fill="{deep}"/>'
                      for dx in (-5.4, -1.8, 1.8, 5.4))
            + f'<path d="M{_n(x - 1.5 * s)} {_n(y + s)}C{_n(x - 2 * s)} {_n(y + 4 * s)} {_n(x - 2.6 * s)} {_n(y + 6.5 * s)} {_n(x - 3.6 * s)} {_n(y + 8.5 * s)}"'
            f' fill="none" stroke="#fff" stroke-opacity=".5" stroke-width=".8"/></g>')


def _bluebell(light, deep):
    defs = _lin('p1', light, deep) + _lin('st', '#8fd3a6', '#2f7a50')
    body = ('<path d="M24 59C22 42 26 22 41 12" fill="none" stroke="url(#st)" stroke-width="1.8" stroke-linecap="round"/>'
            + _at('pointed', (-34, -10, 22), 24, 59, 0, 21, 4.2, 'url(#lf)'))
    for x, y, lean, sx, sy in ((19, 31, 8, 23.6, 30), (27.5, 20.5, 2, 27.6, 19), (38, 14.5, -6, 37, 13)):
        body += f'<path d="M{_n(sx)} {_n(sy)}C{_n(sx - 1)} {_n(sy - .5)} {_n(x + 1)} {_n(y - 2.4)} {_n(x)} {_n(y)}" fill="none" stroke="#2f7a50" stroke-width="1.1"/>'
    for x, y, lean, s in ((19, 31, 8, 1.25), (27.5, 20.5, 2, 1.3), (38, 14.5, -6, 1.15)):
        body += _bell(x + (6 if x > 30 else 4), y + 2, lean, s, deep)
    return defs, body


def _wildflower(light, deep):
    defs = _lin('p1', light, deep) + _lin('p2', '#e6eeff', '#8ea4e6') + _lin('st', '#8fd3a6', '#2f7a50')
    body = ''.join(f'<path d="{d}" fill="none" stroke="url(#st)" stroke-width="1.2" stroke-linecap="round"/>'
                   for d in ('M24 57C24 46 23 36 22 27', 'M33 57C34 46 37 32 40 21', 'M36 57C36 50 36 45 35 40',
                             'M16 58C18 52 19 48 18 44', 'M47 58C46 52 47 49 49 45'))
    for (x, y, fill, s) in ((22, 25, 'url(#p1)', 1), (40, 19, 'url(#p2)', 1.05), (35, 39, 'url(#p1)', .85)):
        body += _ring('round', 5, 1.2 * s, 7.5 * s, 5.4 * s, fill, cx=x, cy=y, offset=18)
        body += f'<circle cx="{_n(x)}" cy="{_n(y)}" r="{_n(2.2 * s)}" fill="#ffd25e"/>'
    body += _dots(3, 0, .9, '#fff7d6', cx=28, cy=33)
    return defs, body


BLOOMS = {
    'rose': _rose, 'daisy': _daisy, 'lotus': _lotus, 'lavender': _lavender, 'tulip': _tulip,
    'iris': _iris, 'bluebell': _bluebell, 'sunflower': _sunflower, 'orchid': _orchid,
    'wildflower': _wildflower,
}


# ---------------------------------------------------------------------------
# growth stages
# ---------------------------------------------------------------------------

def _scaled(body, k, cx, cy):
    return f'<g transform="translate({_n(cx)} {_n(cy)}) scale({k}) translate({_n(-cx)} {_n(-cy)})">{body}</g>'


def _tint(deep, cy=34, r=22, alpha=.42):
    """A soft pool of the flower's colour behind a young plant, so even a
    seed carries its category at a glance."""
    return (f'<radialGradient id="tn" cx="50%" cy="50%" r="50%"><stop offset="0" stop-color="{deep}" stop-opacity="{alpha}"/>'
            f'<stop offset="1" stop-color="{deep}" stop-opacity="0"/></radialGradient>',
            f'<circle cx="32" cy="{cy}" r="{r}" fill="url(#tn)"/>')


def _seed(light, deep):
    defs = _lin('sd', '#e2b07a', '#8a5a2b', x1=0, y1=0, x2=1, y2=1) + _rad('sp', light, deep, cy='50%', r='50%')
    body = (_soil()
            + '<ellipse cx="32" cy="44" rx="5" ry="7" fill="url(#sd)" transform="rotate(-18 32 44)"/>'
            + '<ellipse cx="30.4" cy="41.6" rx="1.3" ry="2.6" fill="#fff" fill-opacity=".38" transform="rotate(-18 30.4 41.6)"/>'
            + f'<circle cx="36" cy="34.5" r="6" fill="{deep}" fill-opacity=".22"/>'
            + '<circle cx="36" cy="34.5" r="2.4" fill="url(#sp)"/>'
            + '<circle cx="35.4" cy="33.9" r=".7" fill="#fff" fill-opacity=".8"/>')
    tdef, tbody = _tint(deep, cy=36, r=20)
    return defs + tdef, tbody + _scaled(body, 1.38, 32, 44)


def _sprout(light, deep):
    defs = _rad('sp', light, deep, cy='45%', r='55%')
    body = (_soil()
            + '<path d="M32 50C32 45 31.4 41 32 35" stroke="#3f9d68" stroke-width="2" fill="none" stroke-linecap="round"/>'
            + _at('round', (-62, 62), 32, 38, 0, 12, 6.8, 'url(#lf)')
            + ''.join(f'<path d="M32 37.5L32 28" stroke="#c9f2d9" stroke-opacity=".5" stroke-width=".7"'
                      f' transform="rotate({a} 32 38)"/>' for a in (-62, 62))
            + '<circle cx="32" cy="33.6" r="2.9" fill="url(#sp)"/>')
    tdef, tbody = _tint(deep, cy=34, r=21)
    return defs + tdef, tbody + _scaled(body, 1.36, 32, 44)


def _sapling(light, deep):
    defs = _lin('bd', light, deep)
    body = (_soil()
            + '<path d="M32 52C32 44 31 36 32 24" stroke="#3f9d68" stroke-width="2" fill="none" stroke-linecap="round"/>'
            + _at('round', (-66, 66), 32, 43, 0, 13, 6.4, 'url(#lf)')
            + _at('round', (-54, 54), 32, 34, 0, 10, 5.2, 'url(#lf)')
            + _at('pointed', (0,), 32, 25, 0, 12, 5.4, 'url(#bd)')
            + _at('pointed', (-30, 30), 32, 25.5, 0, 6.5, 2.6, '#3f9d68')
            + '<path d="M31 22c-.3-2.2.2-4.4 1.2-6" stroke="#fff" stroke-opacity=".45" stroke-width=".7" fill="none"/>')
    tdef, tbody = _tint(deep, cy=26, r=17, alpha=.5)
    return defs + tdef, tbody + _scaled(body, 1.12, 32, 40)


def plant_svg(flower, stage):
    """A complete 64x64 SVG for `flower` at `stage`."""
    if flower not in FLOWERS:
        flower = 'wildflower'
    if stage not in STAGES:
        stage = 'seed'
    _name, light, deep = FLOWERS[flower]
    draw = {'seed': _seed, 'sprout': _sprout, 'sapling': _sapling}.get(stage) or BLOOMS[flower]
    defs, body = draw(light, deep)
    base_defs = (
        '<radialGradient id="bg" cx="50%" cy="40%" r="66%">'
        '<stop offset="0" stop-color="#2b7a5b"/><stop offset=".58" stop-color="#145039"/>'
        '<stop offset="1" stop-color="#0a3124"/></radialGradient>'
        + _rad('gl', '#d8ffe9', '#d8ffe9', cy='42%', r='50%').replace(
            '<stop offset="1" stop-color="#d8ffe9"/>', '<stop offset="1" stop-color="#d8ffe9" stop-opacity="0"/>')
        + _lin('lf', LEAF[0], LEAF[1])
        + _rad('sl', '#6b5038', '#2c2015', cy='30%', r='70%')
    )
    title = f'{flower_name(flower)} - {STAGE_LABELS[stage].lower()}'
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" width="64" height="64">'
        f'<title>{title}</title><defs>{base_defs}{defs}</defs>'
        '<rect width="64" height="64" fill="url(#bg)"/>'
        '<circle cx="32" cy="28" r="24" fill="url(#gl)" fill-opacity=".16"/>'
        f'{body}</svg>\n'
    )

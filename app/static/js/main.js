let gardenNetwork = null;
let focusNetwork = null;
let gardenNodesDataSet = null;
let gardenEdgesDataSet = null;
let allNodes = [];
let allEdges = [];
let selectedNode = null;
let gardenLabelsVisible = true;

// Emphasis state: a click or a search pins an emphasis (gardenSelection);
// hovering previews a softer one only while nothing is pinned.
let gardenSelection = null;
let gardenHoverId = null;
let gardenDragging = false;
let gardenTweenFrame = null;
const gardenNodeAlpha = new Map();
const gardenEdgeAlpha = new Map();

// Category order/slugs come from app/services/category_service.py via a JSON
// data block in base.html, so the client list can't drift from the server's.
function readGardenCategories() {
    const el = document.getElementById('gardenCategories');
    if (!el) return [];
    try {
        return JSON.parse(el.textContent) || [];
    } catch (e) {
        return [];
    }
}

const GARDEN_CATEGORIES = readGardenCategories();
const GARDEN_CATEGORY_ORDER = GARDEN_CATEGORIES.map(c => c.value);
const GARDEN_LABEL_ZOOM_THRESHOLD = 0.8;
const GARDEN_NODE_DIM_OPACITY = 0.12;
const GARDEN_EDGE_DIM_OPACITY = 0.08;
const GARDEN_HOVER_NODE_DIM_OPACITY = 0.4;
const GARDEN_HOVER_EDGE_DIM_OPACITY = 0.2;
const GARDEN_EDGE_BASE_OPACITY = 0.6;
// Motion budget for the canvas: emphasis fades and growth entrances are
// per-frame DataSet updates, so very large gardens skip the tween and jump.
const GARDEN_EMPHASIS_MS = 180;
const GARDEN_GROW_MS = 750;
const GARDEN_GROW_START_SCALE = 0.2;
const GARDEN_MAX_TWEEN_ITEMS = 600;
const GARDEN_CAMERA_ANIMATION = { duration: 500, easingFunction: 'easeInOutCubic' };
// Fitting leaves this much breathing room so the floating dock and legend
// sit over open ground rather than over plants.
const GARDEN_FIT_MARGIN = 0.86;
const GARDEN_ZOOM_STEP = 1.3;
const GARDEN_HINT_MS = 9000;

function prefersReducedMotion() {
    return Boolean(window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches);
}

function cameraAnimation() {
    return prefersReducedMotion() ? false : GARDEN_CAMERA_ANIMATION;
}

function easeOutCubic(t) {
    return 1 - Math.pow(1 - t, 3);
}

// Slight overshoot, so a new note "springs" up like a shoot rather than scaling linearly.
function easeOutBack(t) {
    const c1 = 1.4;
    const c3 = c1 + 1;
    return 1 + c3 * Math.pow(t - 1, 3) + c1 * Math.pow(t - 1, 2);
}

function themeColor(varName, fallback, el = document.documentElement) {
    const value = getComputedStyle(el).getPropertyValue(varName).trim();
    return value || fallback;
}

// The garden is an always-dark environment (data-bs-theme="dark" on its
// container), so its canvas colours are read from there, not from <html>.
function gardenScope() {
    return document.getElementById('gardenGraph') || document.getElementById('focusGraph') || document.documentElement;
}

// Read at use time (not once at render) so a theme toggle recolors edges too.
function gardenEdgeColors() {
    const scope = gardenScope();
    return {
        base: themeColor('--garden-edge', '#4f8f76', scope),
        highlight: themeColor('--garden-edge-highlight', '#b8e8ce', scope),
        hover: themeColor('--garden-edge-hover', '#8fddb8', scope)
    };
}

// themeColor() itself is theme-aware, but it's only ever read once, when a
// graph is first constructed. Toggling dark mode afterward doesn't touch an
// already-drawn vis-network instance, so labels drawn in one theme stay that
// color after switching - this recomputes the font (color + a halo stroke,
// since flat text over graph lines/edges needs the contrast either way) and
// is called both at initial render and again from the toggle handler.
function gardenLabelFont() {
    return {
        size: 14,
        face: '"Times New Roman", Times, "Liberation Serif", serif',
        color: themeColor('--garden-label', '#eaf7f0', gardenScope()),
        strokeWidth: 4,
        strokeColor: 'rgba(4, 24, 17, 0.9)'
    };
}

const GARDEN_CATEGORY_BADGE_CLASS = Object.fromEntries(
    GARDEN_CATEGORIES.map(c => [c.value, `badge-category-${c.slug}`])
);

function gardenCategoryBadgeClass(category) {
    return GARDEN_CATEGORY_BADGE_CLASS[category] || 'badge-category-none';
}

function hexToRgba(hex, alpha) {
    const clean = hex.replace('#', '');
    const full = clean.length === 3 ? clean.split('').map(c => c + c).join('') : clean;
    const num = parseInt(full, 16);
    const r = (num >> 16) & 255;
    const g = (num >> 8) & 255;
    const b = num & 255;
    return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}

// Notes in the same category start near a shared anchor on a ring, then
// physics takes over. Cheaper and less fragile than vis clustering, which
// would merge nodes and complicate click/highlight/search handling.
function seedGardenPositions(nodes, growingIds) {
    const present = [...new Set(nodes.map(n => n.category))];
    const ordered = GARDEN_CATEGORY_ORDER.filter(c => present.includes(c))
        .concat(present.filter(c => !GARDEN_CATEGORY_ORDER.includes(c)));
    const angleStep = (2 * Math.PI) / Math.max(1, ordered.length);
    const ringRadius = 260;
    const clusterSpread = 90;

    const anchors = {};
    ordered.forEach((cat, i) => {
        anchors[cat] = i * angleStep;
    });

    return nodes.map(n => {
        const angle = anchors[n.category] !== undefined ? anchors[n.category] : Math.random() * 2 * Math.PI;
        const cx = ringRadius * Math.cos(angle);
        const cy = ringRadius * Math.sin(angle);
        const localAngle = Math.random() * 2 * Math.PI;
        const localRadius = Math.random() * clusterSpread;
        const seeded = {
            ...n,
            x: cx + localRadius * Math.cos(localAngle),
            y: cy + localRadius * Math.sin(localAngle),
            // shape/image/color/borderWidth come from the server
            // (growth-stage icon + category or pinned-gold ring) - only
            // borderWidthSelected still needs computing client-side, kept
            // relative to whatever borderWidth the payload set so a pinned
            // note's already-thicker ring gets thicker still on selection.
            borderWidthSelected: (n.borderWidth || 2) + 1
        };
        // New notes start as a small seed and grow in once the layout settles.
        if (growingIds.has(n.id)) seeded.size = (n.size || 20) * GARDEN_GROW_START_SCALE;
        return seeded;
    });
}

// "New" means added since this browser last opened the garden for this
// user. The very first visit only records a baseline - nothing animates.
function gardenSeenKey() {
    const container = document.getElementById('gardenGraph');
    return `tg.gardenSeen.${container ? container.dataset.userId : ''}`;
}

// Returns {planted, advanced}: notes new since the last visit, and notes
// whose growth stage moved on (seed -> sprout etc.) since then. Stored as
// {id: stage}; an older plain id list is still read, just without stages.
function takeGardenChanges(nodes) {
    const none = { planted: new Set(), advanced: new Set() };
    let seen = null;
    try {
        const raw = localStorage.getItem(gardenSeenKey());
        if (raw) {
            const parsed = JSON.parse(raw);
            seen = Array.isArray(parsed) ? Object.fromEntries(parsed.map(id => [id, null])) : parsed;
        }
        localStorage.setItem(gardenSeenKey(), JSON.stringify(Object.fromEntries(nodes.map(n => [n.id, n.stage]))));
    } catch (e) {
        return none;
    }
    if (!seen || prefersReducedMotion() || nodes.length > GARDEN_MAX_TWEEN_ITEMS) return none;
    const order = ['seed', 'sprout', 'sapling', 'tree'];
    return {
        planted: new Set(nodes.filter(n => !(n.id in seen)).map(n => n.id)),
        advanced: new Set(nodes.filter(n => n.id in seen && seen[n.id]
            && order.indexOf(n.stage) > order.indexOf(seen[n.id])).map(n => n.id))
    };
}

// Planting: new notes spring up from a seed with a ripple in the soil;
// notes that reached a new growth stage swell once and ripple in gold-green.
function growGardenNodes(changes) {
    if (!gardenNodesDataSet) return;
    const planted = allNodes.filter(n => changes.planted.has(n.id));
    const advanced = allNodes.filter(n => changes.advanced.has(n.id));
    if (!planted.length && !advanced.length) return;
    gardenGrowing = true;
    planted.forEach((n, i) => addGardenRipple(n.id, 'rgba(184, 232, 206, ', i * 90));
    advanced.forEach((n, i) => addGardenRipple(n.id, 'rgba(221, 190, 110, ', i * 90));
    const start = performance.now();
    function step(now) {
        const p = Math.min(1, (now - start) / GARDEN_GROW_MS);
        const plantScale = p >= 1 ? 1 : GARDEN_GROW_START_SCALE + (1 - GARDEN_GROW_START_SCALE) * easeOutBack(p);
        const pulse = p >= 1 ? 1 : 1 + 0.22 * Math.sin(Math.PI * p);
        gardenNodesDataSet.update(
            planted.map(n => ({ id: n.id, size: (n.size || 20) * plantScale }))
                .concat(advanced.map(n => ({ id: n.id, size: (n.size || 20) * pulse })))
        );
        if (p < 1) {
            requestAnimationFrame(step);
        } else {
            gardenGrowing = false;
        }
    }
    requestAnimationFrame(step);
}

// ---------------------------------------------------------------------------
// Garden atmosphere - drawn beneath the nodes on each frame vis renders.
// Nothing here runs continuously: halos are drawn only when vis redraws
// anyway, and the short-lived effects (light flowing along a selected
// note's connections, planting ripples, the idle breeze) each stop on
// their own. Drawn in `beforeDrawing`, so node rings are never painted over.
// ---------------------------------------------------------------------------

const GARDEN_FLOW_MS = 2600;
const GARDEN_RIPPLE_MS = 1500;
const GARDEN_BREEZE_IDLE_MS = 5000;
const GARDEN_BREEZE_SETTLE_MS = 6000;
const GARDEN_BREEZE_EVERY_MS = 7000;
const GARDEN_BREEZE_MS = 1200;
const GARDEN_MAX_AMBIENT_NODES = 200;

let gardenFlow = null;
let gardenAtmosphereFrame = null;
const gardenRipples = [];
const gardenHiddenIds = new Set();
let gardenGrowing = false;
let gardenSettledAt = 0;
let gardenLastActivity = 0;
let gardenBreeze = null;

function gardenNodeById(id) {
    return allNodes.find(n => n.id === id);
}

// A halo that starts just outside the node's ring and fades outward. It is
// an annulus on purpose: nothing is ever painted underneath the node, so a
// node's own fill and category/pinned ring look identical with or without it.
function gardenGlow(ctx, x, y, nodeSize, reach, rgb, alpha) {
    const inner = nodeSize + 3;
    const outer = nodeSize * reach;
    const g = ctx.createRadialGradient(x, y, inner, x, y, outer);
    g.addColorStop(0, `rgba(${rgb}, ${alpha})`);
    g.addColorStop(1, `rgba(${rgb}, 0)`);
    ctx.fillStyle = g;
    ctx.beginPath();
    ctx.arc(x, y, outer, 0, Math.PI * 2);
    ctx.arc(x, y, inner, 0, Math.PI * 2, true);
    ctx.fill('evenodd');
}

function gardenEdgePoint(edge, t) {
    // Follows vis's own smooth curve when available, else a straight line.
    try {
        const body = gardenNetwork.body.edges[edge.id];
        if (body && body.edgeType && body.edgeType.getPoint) return body.edgeType.getPoint(t);
    } catch (e) { /* fall through */ }
    const pos = gardenNetwork.getPositions([edge.from, edge.to]);
    const a = pos[edge.from], b = pos[edge.to];
    return { x: a.x + (b.x - a.x) * t, y: a.y + (b.y - a.y) * t };
}

function drawGardenAtmosphere(ctx) {
    if (!gardenNetwork) return;
    const now = performance.now();
    const visible = allNodes.filter(n => !gardenHiddenIds.has(n.id));
    const positions = gardenNetwork.getPositions(visible.map(n => n.id));
    const alphaOf = id => (gardenNodeAlpha.has(id) ? gardenNodeAlpha.get(id) : 1);
    ctx.save();

    // pinned notes carry a faint gold aura
    visible.forEach(n => {
        if (!n.is_pinned || !positions[n.id]) return;
        gardenGlow(ctx, positions[n.id].x, positions[n.id].y, (n.size || 20), 2, '221, 178, 98', 0.26 * alphaOf(n.id));
    });

    // search matches glow softly
    if (gardenSelection && gardenSelection.kind === 'search') {
        gardenSelection.nodes.forEach(id => {
            const n = gardenNodeById(id);
            if (n && positions[id]) gardenGlow(ctx, positions[id].x, positions[id].y, (n.size || 20), 2.2, '184, 232, 206', 0.4);
        });
    }

    // hovered note: a pool of mint light
    if (gardenHoverId !== null && positions[gardenHoverId]) {
        const n = gardenNodeById(gardenHoverId);
        if (n) gardenGlow(ctx, positions[n.id].x, positions[n.id].y, (n.size || 20), 2.3, '184, 232, 206', 0.34);
    }

    // selected note: a stronger halo that breathes while light flows out
    if (gardenSelection && gardenSelection.kind === 'node' && positions[gardenSelection.nodeId]) {
        const n = gardenNodeById(gardenSelection.nodeId);
        const breathing = gardenFlow ? 0.12 * Math.sin((now - gardenFlow.start) / 260) : 0;
        if (n) gardenGlow(ctx, positions[n.id].x, positions[n.id].y, (n.size || 20), 2.6, '143, 221, 184', 0.5 + breathing);
    }

    // light flowing along the selected note's connections
    if (gardenFlow) {
        const elapsed = now - gardenFlow.start;
        const fade = Math.max(0, Math.min(1, (GARDEN_FLOW_MS - elapsed) / 500));
        ctx.shadowColor = 'rgba(205, 255, 220, 0.9)';
        ctx.shadowBlur = 8;
        gardenFlow.edges.forEach(edge => {
            if (gardenHiddenIds.has(edge.from) || gardenHiddenIds.has(edge.to)) return;
            const outward = edge.from === gardenFlow.nodeId;
            for (let k = 0; k < 3; k++) {
                const t = ((elapsed / 1100) + k / 3) % 1;
                const p = gardenEdgePoint(edge, outward ? t : 1 - t);
                ctx.fillStyle = `rgba(214, 255, 228, ${(0.85 * fade * Math.sin(Math.PI * t)).toFixed(3)})`;
                ctx.beginPath();
                ctx.arc(p.x, p.y, 3.2, 0, Math.PI * 2);
                ctx.fill();
            }
        });
        ctx.shadowBlur = 0;
    }

    // planting / growth ripples in the soil
    gardenRipples.forEach(r => {
        const p = (now - r.start) / GARDEN_RIPPLE_MS;
        if (p < 0 || p > 1 || !positions[r.nodeId]) return;
        const n = gardenNodeById(r.nodeId);
        const base = (n && n.size) || 20;
        for (let k = 0; k < 2; k++) {
            const q = p - k * 0.18;
            if (q <= 0) continue;
            ctx.strokeStyle = `${r.rgba}${(0.7 * (1 - q)).toFixed(3)})`;
            ctx.lineWidth = 2;
            ctx.beginPath();
            ctx.arc(positions[r.nodeId].x, positions[r.nodeId].y, base * (1 + q * 2.4), 0, Math.PI * 2);
            ctx.stroke();
        }
    });

    ctx.restore();
}

// Keeps vis redrawing only while a short-lived effect is in flight.
function runGardenAtmosphere() {
    if (gardenAtmosphereFrame !== null || !gardenNetwork) return;
    function tick() {
        const now = performance.now();
        if (gardenFlow && now - gardenFlow.start > GARDEN_FLOW_MS) gardenFlow = null;
        for (let i = gardenRipples.length - 1; i >= 0; i--) {
            if (now - gardenRipples[i].start > GARDEN_RIPPLE_MS) gardenRipples.splice(i, 1);
        }
        gardenNetwork.redraw();
        gardenAtmosphereFrame = (gardenFlow || gardenRipples.length) ? requestAnimationFrame(tick) : null;
    }
    gardenAtmosphereFrame = requestAnimationFrame(tick);
}

function addGardenRipple(nodeId, rgba, delay = 0) {
    if (prefersReducedMotion()) return;
    gardenRipples.push({ nodeId, rgba, start: performance.now() + delay });
    runGardenAtmosphere();
}

function startGardenFlow(nodeId) {
    if (prefersReducedMotion() || (allNodes.length + allEdges.length) > GARDEN_MAX_TWEEN_ITEMS) return;
    const edges = allEdges.filter(e => e.from === nodeId || e.to === nodeId);
    if (!edges.length) return;
    gardenFlow = { nodeId, edges, start: performance.now() };
    runGardenAtmosphere();
}

// Idle breeze: after a quiet moment, a few plants lean gently, then settle.
// Any pointer or key activity ends it instantly and restores exact sizes.
function gardenBreezeAllowed() {
    const now = performance.now();
    return Boolean(gardenNetwork && gardenSettledAt && !gardenBreeze && !gardenGrowing && !gardenDragging
        && !gardenSelection && gardenHoverId === null && !document.hidden && !prefersReducedMotion()
        && allNodes.length <= GARDEN_MAX_AMBIENT_NODES
        && now - gardenSettledAt > GARDEN_BREEZE_SETTLE_MS
        && now - gardenLastActivity > GARDEN_BREEZE_IDLE_MS);
}

function startGardenBreeze() {
    if (!gardenBreezeAllowed()) return;
    const pool = allNodes.filter(n => !gardenHiddenIds.has(n.id));
    const targets = pool.sort(() => Math.random() - 0.5).slice(0, 3);
    if (!targets.length) return;
    const start = performance.now();
    gardenBreeze = { targets, frame: null };
    function step(now) {
        if (!gardenBreeze) return;
        const p = Math.min(1, (now - start) / GARDEN_BREEZE_MS);
        gardenNodesDataSet.update(targets.map((n, i) => {
            const local = Math.min(1, Math.max(0, p * 1.4 - i * 0.2));
            return { id: n.id, size: (n.size || 20) * (1 + 0.07 * Math.sin(Math.PI * local)) };
        }));
        if (p < 1) {
            gardenBreeze.frame = requestAnimationFrame(step);
        } else {
            endGardenBreeze();
        }
    }
    gardenBreeze.frame = requestAnimationFrame(step);
}

function endGardenBreeze() {
    if (!gardenBreeze) return;
    if (gardenBreeze.frame) cancelAnimationFrame(gardenBreeze.frame);
    gardenNodesDataSet.update(gardenBreeze.targets.map(n => ({ id: n.id, size: n.size || 20 })));
    gardenBreeze = null;
    if (gardenNetwork) gardenNetwork.redraw();
}

function initGardenAmbience() {
    gardenLastActivity = performance.now();
    const activity = () => {
        gardenLastActivity = performance.now();
        endGardenBreeze();
    };
    ['pointermove', 'pointerdown', 'keydown', 'wheel', 'touchstart'].forEach(type =>
        window.addEventListener(type, activity, { passive: true, capture: true }));
    setInterval(startGardenBreeze, GARDEN_BREEZE_EVERY_MS);
}

function initGarden() {
    fetch('/garden/data')
        .then(response => response.json())
        .then(data => {
            allNodes = data.nodes;
            allEdges = data.edges;
            updateGardenStats();
            const empty = document.getElementById('gardenEmpty');
            if (empty) empty.classList.toggle('d-none', allNodes.length > 0);
            renderGraph(allNodes, allEdges, takeGardenChanges(allNodes));
        })
        .catch(error => console.error('Error loading garden data:', error));
}

function renderGraph(nodes, edges, changes) {
    const container = document.getElementById('gardenGraph');
    if (!container) return;

    const edgeColors = gardenEdgeColors();

    const options = {
        nodes: {
            shape: 'dot',
            size: 20,
            font: gardenLabelFont(),
            borderWidth: 2,
            shadow: { enabled: true, color: 'rgba(0, 0, 0, 0.5)', size: 14, x: 0, y: 5 },
            // Without this, vis-network's default selection style replaces a
            // clicked node's real color/border (category ring, pinned gold
            // ring) with a flat blue highlight - wiping the exact visual
            // distinction those are there to make, on the single most common
            // interaction with the graph. The app already gives its own
            // selection feedback (applyGardenEmphasis dims everything not
            // connected), so vis's own highlight is redundant as well as
            // destructive - disabled outright rather than reimplemented.
            chosen: false
        },
        edges: {
            smooth: {
                type: 'continuous',
                roundness: 0.5
            },
            color: {
                color: edgeColors.base,
                highlight: edgeColors.highlight,
                hover: edgeColors.hover,
                opacity: GARDEN_EDGE_BASE_OPACITY
            },
            hoverWidth: 0.8,
            selectionWidth: 0,
            shadow: false
        },
        physics: {
            enabled: true,
            solver: 'forceAtlas2Based',
            forceAtlas2Based: {
                gravitationalConstant: -65,
                centralGravity: 0.012,
                springLength: 165,
                springConstant: 0.08,
                damping: 0.4,
                avoidOverlap: 0.35
            },
            stabilization: {
                enabled: true,
                iterations: 1000,
                updateInterval: 25,
                fit: false
            }
        },
        interaction: {
            hover: true,
            tooltipDelay: 200,
            zoomView: true,
            dragView: true,
            multiselect: false
        }
    };

    gardenLabelsVisible = true;
    gardenSelection = null;
    gardenHoverId = null;
    gardenNodeAlpha.clear();
    gardenEdgeAlpha.clear();
    gardenNodesDataSet = new vis.DataSet(seedGardenPositions(nodes, changes.planted));
    gardenEdgesDataSet = new vis.DataSet(edges);
    // Edges arrive from the server without an id; vis.DataSet assigns one
    // on insert. Re-read them back out so later per-edge .update() calls
    // (highlight/dim) have real ids to target.
    allEdges = gardenEdgesDataSet.get();

    const dataset = {
        nodes: gardenNodesDataSet,
        edges: gardenEdgesDataSet
    };

    gardenNetwork = new vis.Network(container, dataset, options);
    gardenNetwork.on('beforeDrawing', drawGardenAtmosphere);

    gardenNetwork.once('stabilizationIterationsDone', function() {
        gardenNetwork.setOptions({ physics: { enabled: false } });
        const toggle = document.getElementById('physicsToggle');
        if (toggle) toggle.checked = false;
        gardenFitView({ animate: false });
        gardenSettledAt = performance.now();
        growGardenNodes(changes);
    });

    gardenNetwork.on('zoom', function() {
        updateGardenLabelVisibility();
    });

    gardenNetwork.on('click', function(params) {
        dismissGardenHint();
        if (params.nodes.length > 0) {
            selectGardenNode(params.nodes[0]);
        } else {
            closePanel();
        }
    });

    gardenNetwork.on('hoverNode', function(params) {
        container.style.cursor = 'pointer';
        if (gardenDragging) return;
        gardenHoverId = params.node;
        // with a note selected, hovering another only adds its halo
        if (gardenSelection) {
            gardenNetwork.redraw();
            return;
        }
        applyGardenEmphasis();
    });

    gardenNetwork.on('blurNode', function() {
        container.style.cursor = 'default';
        if (gardenHoverId === null) return;
        gardenHoverId = null;
        if (!gardenSelection && !gardenDragging) {
            applyGardenEmphasis();
        } else {
            gardenNetwork.redraw();
        }
    });

    // vis only fires blurNode on a canvas mousemove, so leaving the canvas
    // straight from a node would otherwise leave the hover preview stuck.
    container.addEventListener('mouseleave', function() {
        if (gardenHoverId === null) return;
        gardenHoverId = null;
        if (!gardenSelection) {
            applyGardenEmphasis();
        } else {
            gardenNetwork.redraw();
        }
    });

    gardenNetwork.on('dragStart', function() {
        gardenDragging = true;
        dismissGardenHint();
    });
    gardenNetwork.on('zoom', dismissGardenHint);
    gardenNetwork.on('dragEnd', function() { gardenDragging = false; });
}

function updateGardenLabelVisibility() {
    if (!gardenNetwork || !gardenNodesDataSet) return;
    const scale = gardenNetwork.getScale();
    const shouldShow = scale > GARDEN_LABEL_ZOOM_THRESHOLD;
    if (shouldShow === gardenLabelsVisible) return;
    gardenLabelsVisible = shouldShow;
    gardenNodesDataSet.update(allNodes.map(node => ({
        id: node.id,
        font: { size: gardenLabelsVisible ? 12 : 0 }
    })));
}

function neighborhoodEmphasis(nodeId, nodeDim, edgeDim) {
    const nodes = new Set(gardenNetwork.getConnectedNodes(nodeId));
    nodes.add(nodeId);
        return {
        kind: 'node',
        nodeId,
        nodes,
        edgeInFocus: edge => edge.from === nodeId || edge.to === nodeId,
        nodeDim,
        edgeDim
    };
}

function searchEmphasis(matchIds) {
    const nodes = new Set(matchIds);
    return {
        kind: 'search',
        nodes,
        edgeInFocus: edge => nodes.has(edge.from) && nodes.has(edge.to),
        nodeDim: GARDEN_NODE_DIM_OPACITY,
        edgeDim: GARDEN_EDGE_DIM_OPACITY
    };
}

function currentGardenEmphasis() {
    if (gardenSelection) return gardenSelection;
    if (gardenHoverId !== null && gardenNodesDataSet.get(gardenHoverId)) {
        return neighborhoodEmphasis(gardenHoverId, GARDEN_HOVER_NODE_DIM_OPACITY, GARDEN_HOVER_EDGE_DIM_OPACITY);
    }
    return null;
}

// node.color is {background, border} (see category_service.category_color()) -
// dim both channels so a de-emphasized node's ring fades too, not just its
// fill. Fully opaque nodes get their original color object back untouched.
function gardenNodeColor(node, alpha) {
    if (alpha >= 1) return node.color;
    return {
        background: hexToRgba(node.color.background, alpha),
        border: hexToRgba(node.color.border, alpha)
    };
}

// Fades every node/edge from its current opacity to the one the current
// emphasis asks for. The last frame always lands on the exact target
// values, so the end state is identical with or without the tween.
function applyGardenEmphasis(animate = true) {
    if (!gardenNetwork || !gardenNodesDataSet || !gardenEdgesDataSet) return;

    const emphasis = currentGardenEmphasis();
    const colors = gardenEdgeColors();
    const nodePlan = allNodes.map(node => ({
        node,
        from: gardenNodeAlpha.has(node.id) ? gardenNodeAlpha.get(node.id) : 1,
        to: !emphasis || emphasis.nodes.has(node.id) ? 1 : emphasis.nodeDim
    }));
    const edgePlan = allEdges.map(edge => {
        const inFocus = emphasis && emphasis.edgeInFocus(edge);
        return {
            edge,
            color: inFocus ? colors.highlight : colors.base,
            from: gardenEdgeAlpha.has(edge.id) ? gardenEdgeAlpha.get(edge.id) : GARDEN_EDGE_BASE_OPACITY,
            to: !emphasis ? GARDEN_EDGE_BASE_OPACITY : (inFocus ? 1 : emphasis.edgeDim)
        };
    });

    function draw(t) {
        const mix = (from, to) => (t >= 1 ? to : from + (to - from) * t);
        gardenNodesDataSet.update(nodePlan.map(({ node, from, to }) => {
            const alpha = mix(from, to);
            gardenNodeAlpha.set(node.id, alpha);
            return { id: node.id, color: gardenNodeColor(node, alpha) };
        }));
        gardenEdgesDataSet.update(edgePlan.map(({ edge, color, from, to }) => {
            const alpha = mix(from, to);
            gardenEdgeAlpha.set(edge.id, alpha);
            return { id: edge.id, color: { color: hexToRgba(color, alpha), opacity: 1 } };
        }));
    }

    if (gardenTweenFrame !== null) cancelAnimationFrame(gardenTweenFrame);
    gardenTweenFrame = null;
    const tween = animate && !prefersReducedMotion()
        && (allNodes.length + allEdges.length) <= GARDEN_MAX_TWEEN_ITEMS;
    if (!tween) {
        draw(1);
        return;
    }

    const start = performance.now();
    function step(now) {
        const p = Math.min(1, (now - start) / GARDEN_EMPHASIS_MS);
        draw(p >= 1 ? 1 : easeOutCubic(p));
        gardenTweenFrame = p < 1 ? requestAnimationFrame(step) : null;
    }
    gardenTweenFrame = requestAnimationFrame(step);
}

// The panel always opens; emphasis and centering only apply when the note
// is actually drawn (a connection can point at a category-filtered node).
function selectGardenNode(nodeId, { center = false } = {}) {
    const node = gardenNodesDataSet && gardenNodesDataSet.get(nodeId);
    if (gardenNetwork && node) {
        gardenSelection = neighborhoodEmphasis(nodeId, GARDEN_NODE_DIM_OPACITY, GARDEN_EDGE_DIM_OPACITY);
        applyGardenEmphasis();
        if (!node.hidden) startGardenFlow(nodeId);
        if (center && !node.hidden) {
            gardenNetwork.focus(nodeId, { scale: gardenNetwork.getScale(), animation: cameraAnimation() });
        }
    }
    showNotePanel(nodeId);
}

function refreshGardenTheme() {
    if (gardenNetwork) {
        const colors = gardenEdgeColors();
        gardenNetwork.setOptions({
            nodes: { font: gardenLabelFont() },
            edges: { color: { highlight: colors.highlight, hover: colors.hover } }
        });
        applyGardenEmphasis(false);
    }
    if (focusNetwork) focusNetwork.setOptions({ nodes: { font: gardenLabelFont() } });
}

function showNotePanel(nodeId) {
    fetch(`/garden/note/${nodeId}`)
        .then(response => response.json())
        .then(note => {
            document.getElementById('notePanel').querySelector('.panel-placeholder').classList.add('d-none');
            const panelContent = document.getElementById('panelContent');
            const wasOpen = selectedNode !== null;
            panelContent.classList.remove('d-none');

            document.getElementById('panelTitle').textContent = note.title;
            const panelCategory = document.getElementById('panelCategory');
            panelCategory.textContent = note.category || 'Uncategorized';
            panelCategory.className = 'badge ' + gardenCategoryBadgeClass(note.category);
            document.getElementById('panelDate').textContent = new Date(note.created_at).toLocaleDateString();
            document.getElementById('panelPreview').textContent = note.content.substring(0, 200) + (note.content.length > 200 ? '...' : '');

            // Note data is user content: build nodes with textContent, never HTML strings.
            document.getElementById('panelTags').replaceChildren(...note.tags.map(tag => {
                const badge = document.createElement('span');
                badge.className = 'tag';
                badge.textContent = tag;
                return badge;
            }));

            const connectionsContainer = document.getElementById('panelConnections');
            if (note.connections.length > 0) {
                connectionsContainer.replaceChildren(...note.connections.map(buildConnectionItem));
            } else {
                const empty = document.createElement('p');
                empty.className = 'text-muted small';
                empty.textContent = 'No connections found';
                connectionsContainer.replaceChildren(empty);
            }

            document.getElementById('panelViewBtn').href = `/notes/${note.id}`;
            const focusBtn = document.getElementById('panelFocusBtn');
            if (focusBtn) focusBtn.href = `/garden/focus/${note.id}`;
            selectedNode = nodeId;

            // Opening from the placeholder animates via CSS; switching from
            // one note to another replays a shorter version of it.
            if (wasOpen && !prefersReducedMotion()) {
                panelContent.animate(
                    [{ opacity: 0.2, translate: '8px 0' }, { opacity: 1, translate: '0 0' }],
                    { duration: 260, easing: 'cubic-bezier(0.22, 1, 0.36, 1)' }
                );
            }
        })
        .catch(error => console.error('Error loading note:', error));
}

function buildConnectionItem(conn) {
    const item = document.createElement('button');
    item.type = 'button';
    item.className = 'connection-item';
    item.addEventListener('click', () => selectGardenNode(conn.id, { center: true }));

    const row = document.createElement('div');
    row.className = 'd-flex justify-content-between align-items-center gap-2';
    const title = document.createElement('strong');
    title.textContent = conn.title.substring(0, 30) + (conn.title.length > 30 ? '...' : '');
    const label = document.createElement('span');
    label.className = 'badge bg-' + (conn.label === 'Strong match' ? 'success' : 'secondary');
    label.textContent = conn.label;
    row.append(title, label);

    const reason = document.createElement('small');
    reason.className = 'connection-reason d-block';
    reason.textContent = conn.reason;

    const category = document.createElement('small');
    category.className = 'text-muted';
    category.textContent = conn.category || 'Uncategorized';

    item.append(row, reason, category);
    return item;
}

function closePanel() {
    const panel = document.getElementById('notePanel');
    if (!panel) return;
    panel.querySelector('.panel-placeholder').classList.remove('d-none');
    document.getElementById('panelContent').classList.add('d-none');
    selectedNode = null;
    gardenFlow = null;
    if (gardenSelection && gardenSelection.kind === 'node') {
        gardenSelection = null;
        applyGardenEmphasis();
    }
}

function searchNode() {
    if (!gardenNetwork) return;
    const input = document.getElementById('searchNode');
    const feedback = document.getElementById('searchFeedback');
    const rawQuery = input.value.trim();
    const query = rawQuery.toLowerCase();

    if (!query) {
        gardenNetwork.selectNodes([]);
        if (feedback) feedback.textContent = '';
        if (gardenSelection && gardenSelection.kind === 'search') {
            gardenSelection = null;
            applyGardenEmphasis();
        }
        return;
    }

    const matchingNodes = allNodes.filter(node =>
        node.label.toLowerCase().includes(query) ||
        node.title.toLowerCase().includes(query)
    );

    if (matchingNodes.length === 0) {
        gardenNetwork.selectNodes([]);
        if (feedback) feedback.textContent = `No notes match "${rawQuery}".`;
        return;
    }

    const matchIds = matchingNodes.map(n => n.id);
    gardenNetwork.selectNodes(matchIds);
    // chosen:false means vis draws no selection of its own - matches stay
    // at full strength while the rest of the garden recedes.
    gardenFlow = null;
    gardenSelection = searchEmphasis(matchIds);
    applyGardenEmphasis();
    gardenFitView({ nodes: matchIds });
    if (feedback) {
        feedback.textContent = matchIds.length === 1
            ? '1 match found.'
            : `${matchIds.length} matches found.`;
    }
}

function applyGardenCategoryFilters() {
    if (!gardenNodesDataSet) return;

    const checkedCategories = Array.from(
        document.querySelectorAll('.garden-category-filter:checked')
    ).map(el => el.value);

    // No boxes checked = show everything (an all-hidden graph would be
    // confusing, and "no filter selected" naturally means "no filtering").
    const updates = allNodes.map(node => ({
        id: node.id,
        hidden: checkedCategories.length > 0 && !checkedCategories.includes(node.category)
    }));

    gardenHiddenIds.clear();
    updates.forEach(u => { if (u.hidden) gardenHiddenIds.add(u.id); });
    gardenNodesDataSet.update(updates);
    updateGardenStats();
}

function clearGardenCategoryFilters() {
    document.querySelectorAll('.garden-category-filter:checked').forEach(box => { box.checked = false; });
    applyGardenCategoryFilters();
}

// "17 plants · 24 connections", or "Showing 6 of 17 plants" while filtered.
// Built from text nodes - the numbers are ours, but keep to one pattern.
function updateGardenStats() {
    const stats = document.getElementById('gardenStats');
    if (!stats) return;
    const strong = text => {
        const el = document.createElement('strong');
        el.textContent = text;
        return el;
    };
    const total = allNodes.length;
    const shown = total - gardenHiddenIds.size;
    const plural = (n, word) => `${word}${n === 1 ? '' : 's'}`;
    if (gardenHiddenIds.size > 0) {
        stats.replaceChildren('Showing ', strong(shown), ` of ${total} ${plural(total, 'plant')}`);
    } else {
        stats.replaceChildren(strong(total), ` ${plural(total, 'plant')} \u00b7 `,
            strong(allEdges.length), ` ${plural(allEdges.length, 'connection')}`);
    }
}

// vis 9 has no fit padding, so fit instantly, read where that landed, put
// the camera back and glide to a slightly wider version of it.
function gardenFitView({ nodes, animate = true } = {}) {
    if (!gardenNetwork) return;
    const from = { position: gardenNetwork.getViewPosition(), scale: gardenNetwork.getScale() };
    gardenNetwork.fit(nodes ? { nodes, animation: false } : { animation: false });
    const to = { position: gardenNetwork.getViewPosition(), scale: gardenNetwork.getScale() * GARDEN_FIT_MARGIN };
    const animation = animate ? cameraAnimation() : false;
    if (animation) gardenNetwork.moveTo({ ...from, animation: false });
    gardenNetwork.moveTo({ ...to, animation });
}

function fitGraph() {
    gardenFitView();
}

// Same as a wheel zoom, including the label hiding the 'zoom' event drives.
// Quick repeated presses build on the previous target, not wherever the
// camera happens to be mid-glide.
let gardenZoomTarget = null;

function zoomGarden(factor) {
    if (!gardenNetwork) return;
    const animation = cameraAnimation();
    const recent = gardenZoomTarget && performance.now() - gardenZoomTarget.at < GARDEN_CAMERA_ANIMATION.duration;
    const scale = (recent ? gardenZoomTarget.scale : gardenNetwork.getScale()) * factor;
    gardenZoomTarget = { scale, at: performance.now() };
    gardenNetwork.moveTo({ scale, animation });
    if (animation) {
        gardenNetwork.once('animationFinished', updateGardenLabelVisibility);
    } else {
        updateGardenLabelVisibility();
    }
}

function dismissGardenHint() {
    const hint = document.getElementById('gardenHint');
    if (hint) hint.classList.add('is-dismissed');
}

// The legend opens by itself only on a first visit with room to spare;
// after that it stays however the user last left it.
function initGardenChrome() {
    const legend = document.getElementById('gardenLegend');
    if (legend) {
        let saved = null;
        try { saved = localStorage.getItem('tg.gardenLegend'); } catch (e) { /* storage blocked */ }
        legend.open = saved ? saved === 'open' : !window.matchMedia('(max-width: 991.98px)').matches;
        legend.addEventListener('toggle', () => {
            try { localStorage.setItem('tg.gardenLegend', legend.open ? 'open' : 'closed'); } catch (e) { /* storage blocked */ }
        });
    }
    setTimeout(dismissGardenHint, GARDEN_HINT_MS);
}

function resetView() {
    if (gardenNetwork) {
        gardenNetwork.moveTo({ position: { x: 0, y: 0 }, scale: 1, animation: cameraAnimation() });
    }
}

function togglePhysics() {
    if (gardenNetwork) {
        const enabled = document.getElementById('physicsToggle').checked;
        gardenNetwork.setOptions({physics: {enabled: enabled}});
    }
}

function initFocusGraph() {
    const container = document.getElementById('focusGraph');
    if (!container) return;
    
    const noteId = container.dataset.noteId;
    const depth = container.dataset.depth || 2;
    const minSimilarity = container.dataset.minSimilarity || 0;
    
    fetch(`/garden/api/focus/${noteId}?depth=${depth}&min_similarity=${minSimilarity}`)
        .then(response => response.json())
        .then(data => {
            renderFocusGraph(container, data.nodes, data.edges);
        })
        .catch(error => console.error('Error loading focus data:', error));
}

function renderFocusGraph(container, nodes, edges) {
    const options = {
        nodes: {
            shape: 'dot',
            font: gardenLabelFont(),
            borderWidth: 2,
            shadow: { enabled: true, color: 'rgba(0, 0, 0, 0.5)', size: 14, x: 0, y: 5 },
            // Same reasoning as renderGraph(): don't let vis-network's default
            // selection style replace a node's real color/border on click.
            chosen: false
        },
        edges: {
            smooth: {
                type: 'continuous',
                roundness: 0.5
            },
            color: {
                color: gardenEdgeColors().base,
                highlight: gardenEdgeColors().highlight,
                hover: gardenEdgeColors().hover
            }
        },
        physics: {
            enabled: true,
            solver: 'forceAtlas2Based',
            forceAtlas2Based: {
                gravitationalConstant: -50,
                centralGravity: 0.01,
                springLength: 150,
                springConstant: 0.08,
                damping: 0.4
            },
            stabilization: {
                enabled: true,
                iterations: 1000
            }
        },
        interaction: {
            hover: true,
            tooltipDelay: 200
        }
    };
    
    const dataset = {
        nodes: new vis.DataSet(nodes),
        edges: new vis.DataSet(edges)
    };

    focusNetwork = new vis.Network(container, dataset, options);
}

function initSearchAutocomplete() {
    const input = document.getElementById('q');
    const box = document.getElementById('searchSuggestions');
    if (!input || !box) return;

    let debounceTimer = null;

    function hideSuggestions() {
        box.style.display = 'none';
        box.innerHTML = '';
    }

    function renderSuggestions(suggestions) {
        box.innerHTML = '';
        suggestions.forEach(function(note) {
            // Note titles/categories are user content: textContent, never innerHTML.
            const item = document.createElement('button');
            item.type = 'button';
            item.className = 'list-group-item list-group-item-action d-flex justify-content-between align-items-center';

            const title = document.createElement('span');
            title.textContent = note.title;
            item.appendChild(title);

            if (note.category) {
                const badge = document.createElement('span');
                badge.className = 'badge ms-2 ' + gardenCategoryBadgeClass(note.category);
                badge.textContent = note.category;
                item.appendChild(badge);
            }

            item.addEventListener('click', function() {
                window.location.href = `/notes/${note.id}`;
            });

            box.appendChild(item);
        });
        box.style.display = suggestions.length ? 'block' : 'none';
    }

    input.addEventListener('input', function() {
        const q = input.value.trim();
        clearTimeout(debounceTimer);
        if (q.length < 2) {
            hideSuggestions();
            return;
        }
        debounceTimer = setTimeout(function() {
            fetch(`/search/api/suggest?q=${encodeURIComponent(q)}`)
                .then(response => response.json())
                .then(renderSuggestions)
                .catch(error => console.error('Error fetching search suggestions:', error));
        }, 200);
    });

    document.addEventListener('click', function(e) {
        if (e.target !== input && !box.contains(e.target)) {
            hideSuggestions();
        }
    });

    input.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') hideSuggestions();
    });
}

function initDarkMode() {
    const toggle = document.getElementById('darkModeToggle');
    const icon = document.getElementById('darkModeIcon');
    const html = document.documentElement;

    // theme-init.js already applied the saved theme; only sync the control.
    function syncToggle() {
        const isDark = html.getAttribute('data-bs-theme') === 'dark';
        if (icon) icon.className = isDark ? 'bi bi-sun' : 'bi bi-moon';
        if (toggle) toggle.setAttribute('aria-pressed', String(isDark));
    }
    syncToggle();

    if (toggle) {
        toggle.addEventListener('click', function() {
            const isDark = html.getAttribute('data-bs-theme') === 'dark';
            html.setAttribute('data-bs-theme', isDark ? 'light' : 'dark');
            localStorage.setItem('darkMode', !isDark);
            syncToggle();
            refreshGardenTheme();
        });
    }
}

function initFlashAutoDismiss() {
    const alerts = document.querySelectorAll('.alert[data-autodismiss]');
    if (!alerts.length) return;
    setTimeout(function() {
        alerts.forEach(function(alert) {
            if (window.bootstrap && bootstrap.Alert) {
                bootstrap.Alert.getOrCreateInstance(alert).close();
            } else {
                alert.remove();
            }
        });
    }, 5000);
}

function csrfToken() {
    const meta = document.querySelector('meta[name="csrf-token"]');
    return meta ? meta.content : '';
}

function initTagSuggestions() {
    const button = document.getElementById('suggestTagsButton');
    const region = document.getElementById('tagSuggestions');
    const form = button && button.closest('form');
    if (!form || !region) return;
    const tagsInput = form.querySelector('[name="tags"]');
    const titleInput = form.querySelector('[name="title"]');
    const contentInput = form.querySelector('[name="content"]');

    function currentTags() {
        return tagsInput.value.split(',').map(t => t.trim()).filter(Boolean);
    }

    function addTag(name, chip) {
        const tags = currentTags();
        if (!tags.some(t => t.toLowerCase() === name.toLowerCase())) tags.push(name);
        tagsInput.value = tags.join(', ');
        chip.remove();
        if (!region.querySelector('button')) region.replaceChildren();
        tagsInput.focus();
    }

    function render(suggestions) {
        region.replaceChildren();
        if (!suggestions.length) {
            const empty = document.createElement('small');
            empty.className = 'text-muted';
            empty.textContent = 'No tag suggestions yet.';
            region.appendChild(empty);
            return;
        }
        const label = document.createElement('small');
        label.className = 'text-muted me-1';
        label.textContent = 'Suggested:';
        region.appendChild(label);
        suggestions.forEach(function(name) {
            const chip = document.createElement('button');
            chip.type = 'button';
            chip.className = 'btn btn-sm btn-outline-primary tag-suggestion me-1 mb-1';
            chip.textContent = name;
            chip.setAttribute('aria-label', `Add tag ${name}`);
            chip.addEventListener('click', () => addTag(name, chip));
            region.appendChild(chip);
        });
    }

    button.addEventListener('click', function() {
        const body = {
            title: titleInput ? titleInput.value : '',
            content: contentInput ? contentInput.value : '',
            tags: tagsInput.value,
        };
        if (button.dataset.noteId) body.note_id = Number(button.dataset.noteId);
        button.disabled = true;
        fetch(button.dataset.suggestUrl, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken() },
            body: JSON.stringify(body),
        })
            .then(response => {
                if (!response.ok) throw new Error(`HTTP ${response.status}`);
                return response.json();
            })
            .then(data => render(data.suggestions || []))
            .catch(error => {
                console.error('Error fetching tag suggestions:', error);
                region.replaceChildren();
                const failed = document.createElement('small');
                failed.className = 'text-danger';
                failed.textContent = 'Could not load tag suggestions.';
                region.appendChild(failed);
            })
            .finally(() => { button.disabled = false; });
    });
}

// Moving between related notes: the page you're leaving lifts away before
// the next one blooms in. Plain left-clicks only; modified clicks (new tab
// etc.) and reduced motion navigate immediately.
function initNoteTransitions() {
    const article = document.querySelector('.note-article');
    if (!article) return;
    document.addEventListener('click', function(e) {
        const link = e.target.closest('a[data-note-link]');
        if (!link || e.defaultPrevented || e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
        if (prefersReducedMotion()) return;
        e.preventDefault();
        let gone = false;
        const go = () => {
            if (gone) return;
            gone = true;
            window.location.href = link.href;
        };
        article.animate([{ opacity: 1, translate: '0 0' }, { opacity: 0, translate: '0 -12px' }],
            { duration: 200, easing: 'cubic-bezier(0.65, 0, 0.35, 1)', fill: 'forwards' }).onfinish = go;
        setTimeout(go, 400);
    });
    // Coming back via the back/forward cache: undo the fade.
    window.addEventListener('pageshow', function(e) {
        if (e.persisted) article.getAnimations().forEach(a => a.cancel());
    });
}

// Garden list view: filter and sort the rendered rows in place - no new
// requests, the server already sent every visible note. Rows that move
// glide to their new place (FLIP); rows that reappear fade up.
const LIBRARY_STAGE_RANK = { seed: 0, sprout: 1, sapling: 2, tree: 3 };
const LIBRARY_SORTS = {
    garden: (a, b) => a.dataset.order - b.dataset.order,
    title: (a, b) => a.dataset.title.localeCompare(b.dataset.title),
    connections: (a, b) => b.dataset.connections - a.dataset.connections || a.dataset.order - b.dataset.order,
    growth: (a, b) => LIBRARY_STAGE_RANK[b.dataset.stage] - LIBRARY_STAGE_RANK[a.dataset.stage]
        || b.dataset.connections - a.dataset.connections,
    recent: (a, b) => b.dataset.updated.localeCompare(a.dataset.updated)
};

function initLibrary() {
    const list = document.getElementById('library');
    const form = document.getElementById('libraryControls');
    if (!list || !form) return;

    const rows = Array.from(list.children);
    const search = document.getElementById('librarySearch');
    const category = document.getElementById('libraryCategory');
    const stage = document.getElementById('libraryStage');
    const sort = document.getElementById('librarySort');
    const count = document.getElementById('libraryCount');
    const noMatch = document.getElementById('libraryNoMatch');
    const noun = n => `note${n === 1 ? '' : 's'}`;

    function apply(animate = true) {
        const query = search.value.trim().toLowerCase();
        const before = new Map(rows.filter(r => !r.hidden).map(r => [r, r.getBoundingClientRect().top]));

        let shown = 0;
        rows.forEach(row => {
            const match = (!query || row.dataset.title.includes(query) || row.dataset.tags.includes(query))
                && (!category.value || row.dataset.category === category.value)
                && (!stage.value || row.dataset.stage === stage.value);
            row.hidden = !match;
            if (match) shown++;
        });
        rows.slice().sort(LIBRARY_SORTS[sort.value] || LIBRARY_SORTS.garden).forEach(row => list.appendChild(row));

        const total = document.createElement('strong');
        total.textContent = shown;
        count.replaceChildren(...(shown === rows.length
            ? [total, ` ${noun(shown)}`]
            : ['Showing ', total, ` of ${rows.length} ${noun(rows.length)}`]));
        list.classList.toggle('d-none', shown === 0);
        noMatch.classList.toggle('d-none', shown > 0);

        if (!animate || prefersReducedMotion()) return;
        rows.forEach(row => {
            if (row.hidden) return;
            const top = row.getBoundingClientRect().top;
            if (!before.has(row)) {
                row.animate([{ opacity: 0, translate: '0 10px' }, { opacity: 1, translate: '0 0' }],
                    { duration: 320, easing: 'cubic-bezier(0.22, 1, 0.36, 1)' });
            } else if (Math.abs(before.get(row) - top) > 1) {
                row.animate([{ translate: `0 ${before.get(row) - top}px` }, { translate: '0 0' }],
                    { duration: 460, easing: 'cubic-bezier(0.22, 1, 0.36, 1)' });
            }
        });
    }

    form.addEventListener('submit', e => e.preventDefault());
    search.addEventListener('input', () => apply());
    [category, stage, sort].forEach(control => control.addEventListener('change', () => apply()));
    document.getElementById('libraryReset').addEventListener('click', () => {
        form.reset();
        apply();
        search.focus();
    });
    apply(false);
}

// Canopy foliage drifts a little slower than the page as you scroll, and
// the hero leaf leans toward the pointer. Desktop pointers only; off under
// reduced motion.
function initParallax() {
    if (prefersReducedMotion()) return;
    const bg = document.querySelector('.canopy-bg');
    const canopy = document.querySelector('.canopy');
    if (bg && canopy && !document.body.classList.contains('page-immersive')) {
        let queued = false;
        const update = () => {
            queued = false;
            const y = window.scrollY;
            if (y > canopy.offsetHeight + 200) return;
            bg.style.setProperty('--parallax', `${(y * 0.28).toFixed(1)}px`);
        };
        window.addEventListener('scroll', () => {
            if (!queued) {
                queued = true;
                requestAnimationFrame(update);
            }
        }, { passive: true });
    }

    const leaf = document.querySelector('[data-parallax-leaf] img');
    if (leaf && window.matchMedia('(pointer: fine)').matches) {
        let frame = null;
        window.addEventListener('pointermove', event => {
            if (frame) return;
            frame = requestAnimationFrame(() => {
                frame = null;
                const x = event.clientX / window.innerWidth - 0.5;
                const y = event.clientY / window.innerHeight - 0.5;
                leaf.style.setProperty('--leaf-x', `${(x * -22).toFixed(1)}px`);
                leaf.style.setProperty('--leaf-y', `${(y * -14).toFixed(1)}px`);
            });
        }, { passive: true });
    }
}

function initConfirmForms() {
    document.querySelectorAll('form[data-confirm]').forEach(function(form) {
        form.addEventListener('submit', function(event) {
            if (!window.confirm(form.dataset.confirm)) {
                event.preventDefault();
                event.stopImmediatePropagation();
            }
        });
    });
}

document.addEventListener('DOMContentLoaded', function() {
    initConfirmForms();
    initDarkMode();
    initSearchAutocomplete();
    initTagSuggestions();

    if (document.getElementById('gardenGraph')) {
        initGarden();
        initGardenAmbience();
        initGardenChrome();
    }
    
    if (document.getElementById('focusGraph')) {
        initFocusGraph();
    }
    
    [
        ['searchNodeButton', searchNode],
        ['fitGraphButton', fitGraph],
        ['resetViewButton', resetView],
        ['zoomInButton', () => zoomGarden(GARDEN_ZOOM_STEP)],
        ['zoomOutButton', () => zoomGarden(1 / GARDEN_ZOOM_STEP)],
        ['clearCategoryFilters', clearGardenCategoryFilters],
        ['closePanelButton', closePanel],
    ].forEach(function([id, handler]) {
        const button = document.getElementById(id);
        if (button) button.addEventListener('click', handler);
    });

    // Escape returns the garden to its resting state.
    if (document.getElementById('gardenGraph')) {
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape' && selectedNode !== null) closePanel();
        });
    }

    const nodeSearch = document.getElementById('searchNode');
    if (nodeSearch) {
        nodeSearch.addEventListener('keydown', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                searchNode();
            }
        });
    }

    document.querySelectorAll('select[data-autosubmit]').forEach(function(select) {
        select.addEventListener('change', () => select.form.submit());
    });

    const physicsToggle = document.getElementById('physicsToggle');
    if (physicsToggle) {
        physicsToggle.addEventListener('change', togglePhysics);
    }

    document.querySelectorAll('.garden-category-filter').forEach(function(checkbox) {
        checkbox.addEventListener('change', applyGardenCategoryFilters);
    });

    initFlashAutoDismiss();
    initParallax();
    initLibrary();
    initNoteTransitions();

    // Saving/importing blocks on relationship scoring, so show progress and
    // disable the submit button (which also prevents double submits).
    document.querySelectorAll('form[data-ai-processing]').forEach(function(form) {
        form.addEventListener('submit', function() {
            if (form.dataset.aiProcessingSubmitted) return;
            form.dataset.aiProcessingSubmitted = 'true';
            form.classList.add('is-submitting');

            const submitBtn = form.querySelector('button[type="submit"], input[type="submit"]');
            if (!submitBtn) return;

            const loadingText = submitBtn.dataset.loadingText || 'Processing...';
            submitBtn.disabled = true;

            if (submitBtn.tagName === 'BUTTON') {
                const spinner = document.createElement('span');
                spinner.className = 'spinner-border spinner-border-sm me-2';
                spinner.setAttribute('aria-hidden', 'true');
                submitBtn.replaceChildren(spinner, document.createTextNode(loadingText));
            } else {
                submitBtn.dataset.originalValue = submitBtn.value;
                submitBtn.value = loadingText;
            }
        });
    });
});

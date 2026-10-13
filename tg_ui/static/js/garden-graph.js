// The Knowledge Garden graph: the full garden (vis-network canvas, halos,
// growth, breeze, the journal side panel) and the focus view. Shared by the
// Flask garden pages and the Streamlit garden component - both load
// tg-core.js, vis-network and this file, then call bootGarden()/initFocusGraph().
// Data and navigation go through `gardenHost`, so neither frontend's URLs
// are baked in here.

// Where the garden gets its data and where its links lead. These defaults
// are the Flask app's routes; the Streamlit component passes its own host to
// configureGarden() (inline data, and actions sent back to Python instead of
// links followed).
let gardenHost = {
    loadGraph: () => fetch('/garden/data').then(response => response.json()),
    loadNote: id => fetch(`/garden/note/${id}`).then(response => response.json()),
    asset: path => `/static/${path}`,
    links: {
        open: id => `/notes/${id}`,
        edit: id => `/notes/${id}/edit`,
        focus: id => `/garden/focus/${id}`
    },
    // (action, noteId) => void. When set, garden links call it instead of navigating.
    navigate: null
};

function configureGarden(host) {
    gardenHost = Object.assign({}, gardenHost, host);
}

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
            borderWidthSelected: (n.borderWidth || 2) + 1,
            // the note's flower at its growth stage (tg_ui/static/img/plants)
            image: n.plant ? gardenHost.asset(n.plant) : n.image
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
const GARDEN_BREEZE_MS = 2200;
const GARDEN_BREEZE_LEAN = 6;
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

// The note's own category hue (its node fill), for its selection halo.
function gardenNodeRgb(node) {
    const background = node.color && node.color.background;
    return /^#[0-9a-f]{3,6}$/i.test(background || '') ? hexToRgb(background) : '143, 221, 184';
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
        if (n) gardenGlow(ctx, positions[n.id].x, positions[n.id].y, (n.size || 20), 2.6, gardenNodeRgb(n), 0.5 + breathing);
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

// Idle breeze: after a quiet moment, a few plants sway - a lean, a smaller
// lean back, then still, like stems in a gust - and swell a touch. Any
// pointer or key activity ends it instantly and restores exact positions
// and sizes.
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
    const home = gardenNetwork.getPositions(targets.map(n => n.id));
    const start = performance.now();
    gardenBreeze = { targets, home, frame: null };
    function step(now) {
        if (!gardenBreeze) return;
        const p = Math.min(1, (now - start) / GARDEN_BREEZE_MS);
        const locals = targets.map((n, i) => Math.min(1, Math.max(0, p * 1.4 - i * 0.2)));
        targets.forEach((n, i) => {
            const lean = Math.sin(locals[i] * Math.PI * 2) * (1 - locals[i]) * GARDEN_BREEZE_LEAN;
            if (home[n.id]) gardenNetwork.moveNode(n.id, home[n.id].x + lean, home[n.id].y - Math.abs(lean) * 0.2);
        });
        gardenNodesDataSet.update(targets.map((n, i) => (
            { id: n.id, size: (n.size || 20) * (1 + 0.05 * Math.sin(Math.PI * locals[i])) }
        )));
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
    const home = gardenBreeze.home || {};
    gardenBreeze.targets.forEach(n => {
        if (home[n.id]) gardenNetwork.moveNode(n.id, home[n.id].x, home[n.id].y);
    });
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
    gardenHost.loadGraph()
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

// The plant image fades with its ring, but never vanishes: a dimmed garden
// still reads as a garden.
function gardenNodeOpacity(alpha) {
    return alpha >= 1 ? 1 : 0.22 + 0.78 * alpha;
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
            return { id: node.id, color: gardenNodeColor(node, alpha), opacity: gardenNodeOpacity(alpha) };
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

const GARDEN_STAGE_LABELS = { seed: 'Seed', sprout: 'Sprout', sapling: 'Sapling', tree: 'In bloom' };
const GARDEN_PREVIEW_CHARS = 520;

function showNotePanel(nodeId) {
    gardenHost.loadNote(nodeId)
        .then(note => renderNotePanel(nodeId, note))
        .catch(error => console.error('Error loading note:', error));
}

function formatGardenDate(iso) {
    const date = new Date(iso);
    return Number.isNaN(date.getTime()) ? '' : date.toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' });
}

// The opening paragraphs of a note as plain text, up to a page's worth.
function previewParagraphs(markdown) {
    const out = [];
    let used = 0;
    for (const block of String(markdown || '').split(/\n\s*\n/)) {
        const text = plainText(block).replace(/\s+/g, ' ').trim();
        if (!text) continue;
        const room = GARDEN_PREVIEW_CHARS - used;
        if (room < 40) break;
        out.push(text.length > room ? `${text.slice(0, room).replace(/\s+\S*$/, '')}…` : text);
        used += text.length;
    }
    return out;
}

// Points a panel action at a note: a real link on the Flask pages, an
// action handed to gardenHost.navigate in the Streamlit component.
function setGardenLink(elementId, action, noteId) {
    const link = document.getElementById(elementId);
    if (!link) return;
    const url = gardenHost.links[action];
    link.href = url ? url(noteId) : '#';
    link.dataset.noteId = noteId;
}

// The selected note, opened like a page in a journal: its plant, title,
// when it was planted and how long it reads, then its opening lines, tags
// and the thoughts it connects to. Note data is user content: every string
// goes in through textContent, never as HTML.
function renderNotePanel(nodeId, note) {
    document.getElementById('notePanel').querySelector('.panel-placeholder').classList.add('d-none');
    const panelContent = document.getElementById('panelContent');
    const wasOpen = selectedNode !== null;
    panelContent.classList.remove('d-none');
    const node = gardenNodeById(nodeId) || {};

    document.getElementById('panelTitle').textContent = note.title;
    const panelCategory = document.getElementById('panelCategory');
    panelCategory.textContent = categoryLabel(note.category);
    panelCategory.className = 'badge ' + gardenCategoryBadgeClass(note.category);

    const plant = document.getElementById('panelPlant');
    if (plant) {
        plant.className = `tg-plant tg-plant--lg tg-hue-${gardenCategorySlug(note.category)}`;
        const img = plant.querySelector('img');
        const src = note.plant || node.plant;
        if (img && src) img.src = gardenHost.asset(src);
    }
    const pinned = document.getElementById('panelPinned');
    if (pinned) pinned.classList.toggle('d-none', !(note.is_pinned || node.is_pinned));

    const meta = document.getElementById('panelMeta');
    if (meta) {
        const parts = [];
        if (note.created_at) parts.push(`Planted ${formatGardenDate(note.created_at)}`);
        parts.push(`${readingMinutes(note.content)} min read`);
        const stage = note.stage || node.stage;
        if (stage && GARDEN_STAGE_LABELS[stage]) parts.push(GARDEN_STAGE_LABELS[stage]);
        meta.replaceChildren();
        parts.forEach((text, i) => {
            if (i) meta.appendChild(tgEl('span', 'tg-sep'));
            meta.appendChild(tgEl('span', i === 2 ? 'tg-stage' : null, text));
        });
    }

    const preview = document.getElementById('panelPreview');
    const paragraphs = previewParagraphs(note.content);
    preview.replaceChildren(...(paragraphs.length
        ? paragraphs.map(text => tgEl('p', null, text))
        : [tgEl('p', 'text-muted', 'This page is still blank.')]));

    const tags = note.tags || [];
    document.getElementById('panelTags').replaceChildren(...tags.map(tag => {
        const item = tgEl('li');
        item.appendChild(tgEl('span', 'tag', tag));
        return item;
    }));
    const tagsSection = document.getElementById('panelTagsSection');
    if (tagsSection) tagsSection.classList.toggle('d-none', tags.length === 0);

    const connectionsContainer = document.getElementById('panelConnections');
    const count = document.getElementById('panelConnectionCount');
    if (count) count.textContent = note.connections.length ? String(note.connections.length) : '';
    if (note.connections.length > 0) {
        connectionsContainer.replaceChildren(...note.connections.map(buildConnectionItem));
    } else {
        connectionsContainer.replaceChildren(tgEl('p', 'text-muted small mb-0',
            'No connections found yet - it will find its neighbours as the garden grows.'));
    }

    setGardenLink('panelViewBtn', 'open', note.id);
    setGardenLink('panelEditBtn', 'edit', note.id);
    setGardenLink('panelFocusBtn', 'focus', note.id);
    selectedNode = nodeId;

    // Opening from the placeholder animates via CSS; switching from one note
    // to another turns the page with a shorter version of it.
    if (wasOpen && !prefersReducedMotion() && panelContent.animate) {
        panelContent.animate(
            [{ opacity: 0.2, translate: '10px 0' }, { opacity: 1, translate: '0 0' }],
            { duration: 280, easing: 'cubic-bezier(0.22, 1, 0.36, 1)' }
        );
    }
}

function buildConnectionItem(conn) {
    const item = tgEl('button', 'connection-item');
    item.type = 'button';
    item.addEventListener('click', () => selectGardenNode(conn.id, { center: true }));

    const other = gardenNodeById(conn.id);
    if (other && other.plant) {
        const img = tgEl('img', 'connection-plant');
        img.src = gardenHost.asset(other.plant);
        img.alt = '';
        img.width = 64;
        img.height = 64;
        item.appendChild(img);
    }

    const body = tgEl('span', 'connection-body');
    const row = tgEl('span', 'connection-top');
    const title = conn.title.length > 48 ? `${conn.title.substring(0, 48)}…` : conn.title;
    row.append(tgEl('strong', 'connection-title', title),
        tgEl('span', 'badge bg-' + (conn.label === 'Strong match' ? 'success' : 'secondary'), conn.label));
    body.append(row,
        tgEl('small', 'connection-reason', conn.reason),
        tgEl('small', 'connection-category', categoryLabel(conn.category)));
    item.appendChild(body);
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
        nodes: new vis.DataSet(nodes.map(n => (n.plant ? { ...n, image: gardenHost.asset(n.plant) } : n))),
        edges: new vis.DataSet(edges)
    };

    focusNetwork = new vis.Network(container, dataset, options);
}

// ---------------------------------------------------------------------------
// Wiring - shared by the Flask garden page and the Streamlit component
// ---------------------------------------------------------------------------

function wireGardenControls() {
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
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && selectedNode !== null) closePanel();
    });

    const nodeSearch = document.getElementById('searchNode');
    if (nodeSearch) {
        nodeSearch.addEventListener('keydown', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                searchNode();
            }
        });
    }

    const physicsToggle = document.getElementById('physicsToggle');
    if (physicsToggle) physicsToggle.addEventListener('change', togglePhysics);

    document.querySelectorAll('.garden-category-filter').forEach(function(checkbox) {
        checkbox.addEventListener('change', applyGardenCategoryFilters);
    });

    // Links marked data-garden-action (open/edit/focus/list/create) go to
    // gardenHost.navigate when the host has one; otherwise they stay links.
    document.addEventListener('click', function(e) {
        const link = e.target.closest('[data-garden-action]');
        if (!link || !gardenHost.navigate) return;
        e.preventDefault();
        const id = link.dataset.noteId ? Number(link.dataset.noteId) : null;
        gardenHost.navigate(link.dataset.gardenAction, id);
    });
}

function bootGarden() {
    if (!document.getElementById('gardenGraph')) return;
    initGarden();
    initGardenAmbience();
    initGardenChrome();
    wireGardenControls();
}

let gardenNetwork = null;
let focusNetwork = null;
let gardenNodesDataSet = null;
let gardenEdgesDataSet = null;
let allNodes = [];
let allEdges = [];
let selectedNode = null;
let gardenLabelsVisible = true;

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

function themeColor(varName, fallback) {
    const value = getComputedStyle(document.documentElement).getPropertyValue(varName).trim();
    return value || fallback;
}

// themeColor() itself is theme-aware, but it's only ever read once, when a
// graph is first constructed. Toggling dark mode afterward doesn't touch an
// already-drawn vis-network instance, so labels drawn in one theme stay that
// color after switching - this recomputes the font (color + a halo stroke,
// since flat text over graph lines/edges needs the contrast either way) and
// is called both at initial render and again from the toggle handler.
function gardenLabelFont() {
    const dark = document.documentElement.getAttribute('data-bs-theme') === 'dark';
    return {
        size: 12,
        face: 'Inter, sans-serif',
        color: themeColor('--text-primary', dark ? '#ece7dc' : '#26332e'),
        strokeWidth: 4,
        strokeColor: dark ? 'rgba(12, 12, 15, 0.85)' : 'rgba(255, 255, 255, 0.92)'
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
function seedGardenPositions(nodes) {
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
        return {
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
    });
}

function initGarden() {
    fetch('/garden/data')
        .then(response => response.json())
        .then(data => {
            allNodes = data.nodes;
            allEdges = data.edges;
            renderGraph(allNodes, allEdges);
        })
        .catch(error => console.error('Error loading garden data:', error));
}

function renderGraph(nodes, edges) {
    const container = document.getElementById('gardenGraph');
    if (!container) return;

    const edgeBaseColor = themeColor('--border-color', '#ded9ca');
    const edgeHighlightColor = themeColor('--primary-color', '#193c32');
    const edgeHoverColor = themeColor('--text-secondary', '#646c67');

    const options = {
        nodes: {
            shape: 'dot',
            size: 20,
            font: gardenLabelFont(),
            borderWidth: 2,
            shadow: { enabled: true, color: 'rgba(0, 0, 0, 0.28)', size: 10, x: 0, y: 4 },
            // Without this, vis-network's default selection style replaces a
            // clicked node's real color/border (category ring, pinned gold
            // ring) with a flat blue highlight - wiping the exact visual
            // distinction those are there to make, on the single most common
            // interaction with the graph. The app already gives its own
            // selection feedback (highlightGardenNeighborhood dims everything
            // not connected), so vis's own highlight is redundant as well as
            // destructive - disabled outright rather than reimplemented.
            chosen: false
        },
        edges: {
            smooth: {
                type: 'continuous',
                roundness: 0.5
            },
            color: {
                color: edgeBaseColor,
                highlight: edgeHighlightColor,
                hover: edgeHoverColor,
                opacity: 0.6
            },
            shadow: false
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
                iterations: 1000,
                updateInterval: 25
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
    gardenNodesDataSet = new vis.DataSet(seedGardenPositions(nodes));
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

    gardenNetwork.once('stabilizationIterationsDone', function() {
        gardenNetwork.setOptions({ physics: { enabled: false } });
        const toggle = document.getElementById('physicsToggle');
        if (toggle) toggle.checked = false;
    });

    gardenNetwork.on('zoom', function() {
        updateGardenLabelVisibility();
    });

    gardenNetwork.on('click', function(params) {
        if (params.nodes.length > 0) {
            const nodeId = params.nodes[0];
            showNotePanel(nodeId);
            highlightGardenNeighborhood(nodeId, edgeHighlightColor, edgeBaseColor);
        } else {
            closePanel();
            clearGardenHighlight(edgeBaseColor);
        }
    });

    gardenNetwork.on('hoverNode', function(params) {
        container.style.cursor = 'pointer';
    });

    gardenNetwork.on('blurNode', function(params) {
        container.style.cursor = 'default';
    });
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

function highlightGardenNeighborhood(nodeId, edgeHighlightColor, edgeBaseColor) {
    if (!gardenNetwork || !gardenNodesDataSet || !gardenEdgesDataSet) return;

    const connected = new Set(gardenNetwork.getConnectedNodes(nodeId));
    connected.add(nodeId);

    gardenNodesDataSet.update(allNodes.map(node => ({
        id: node.id,
        // node.color is {background, border} (see category_service.category_color()) -
        // dim both channels so a de-emphasized node's ring fades too, not
        // just its fill.
        color: connected.has(node.id) ? node.color : {
            background: hexToRgba(node.color.background, GARDEN_NODE_DIM_OPACITY),
            border: hexToRgba(node.color.border, GARDEN_NODE_DIM_OPACITY)
        }
    })));

    gardenEdgesDataSet.update(allEdges.map(edge => {
        const inFocus = edge.from === nodeId || edge.to === nodeId;
        return {
            id: edge.id,
            color: {
                color: inFocus ? edgeHighlightColor : hexToRgba(edgeBaseColor, GARDEN_EDGE_DIM_OPACITY),
                opacity: 1
            }
        };
    }));
}

function clearGardenHighlight(edgeBaseColor) {
    if (!gardenNodesDataSet || !gardenEdgesDataSet) return;
    gardenNodesDataSet.update(allNodes.map(node => ({ id: node.id, color: node.color })));
    gardenEdgesDataSet.update(allEdges.map(edge => ({
        id: edge.id,
        color: { color: edgeBaseColor, opacity: 0.6 }
    })));
}

function showNotePanel(nodeId) {
    fetch(`/garden/note/${nodeId}`)
        .then(response => response.json())
        .then(note => {
            document.getElementById('notePanel').querySelector('.panel-placeholder').classList.add('d-none');
            const panelContent = document.getElementById('panelContent');
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
                badge.className = 'badge bg-light text-dark me-1';
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
            selectedNode = nodeId;
        })
        .catch(error => console.error('Error loading note:', error));
}

function buildConnectionItem(conn) {
    const item = document.createElement('button');
    item.type = 'button';
    item.className = 'connection-item';
    item.addEventListener('click', () => showNotePanel(conn.id));

    const row = document.createElement('div');
    row.className = 'd-flex justify-content-between align-items-center';
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
    document.getElementById('notePanel').querySelector('.panel-placeholder').classList.remove('d-none');
    document.getElementById('panelContent').classList.add('d-none');
    selectedNode = null;
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
    gardenNetwork.fit({ nodes: matchIds, animation: true });
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

    gardenNodesDataSet.update(updates);
}

function fitGraph() {
    if (gardenNetwork) {
        gardenNetwork.fit({animation: true});
    }
}

function resetView() {
    if (gardenNetwork) {
        gardenNetwork.moveTo({position: {x: 0, y: 0}, scale: 1, animation: true});
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
            shadow: { enabled: true, color: 'rgba(0, 0, 0, 0.28)', size: 10, x: 0, y: 4 },
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
                color: themeColor('--border-color', '#ded9ca'),
                highlight: themeColor('--primary-color', '#193c32'),
                hover: themeColor('--text-secondary', '#646c67')
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
                badge.className = 'badge bg-light text-dark ms-2';
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
            if (gardenNetwork) gardenNetwork.setOptions({ nodes: { font: gardenLabelFont() } });
            if (focusNetwork) focusNetwork.setOptions({ nodes: { font: gardenLabelFont() } });
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
    }
    
    if (document.getElementById('focusGraph')) {
        initFocusGraph();
    }
    
    [
        ['searchNodeButton', searchNode],
        ['fitGraphButton', fitGraph],
        ['resetViewButton', resetView],
        ['closePanelButton', closePanel],
    ].forEach(function([id, handler]) {
        const button = document.getElementById(id);
        if (button) button.addEventListener('click', handler);
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

    // Saving/importing blocks on relationship scoring, so show progress and
    // disable the submit button (which also prevents double submits).
    document.querySelectorAll('form[data-ai-processing]').forEach(function(form) {
        form.addEventListener('submit', function() {
            if (form.dataset.aiProcessingSubmitted) return;
            form.dataset.aiProcessingSubmitted = 'true';

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

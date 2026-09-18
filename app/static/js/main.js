let gardenNetwork = null;
let gardenNodesDataSet = null;
let gardenEdgesDataSet = null;
let allNodes = [];
let allEdges = [];
let selectedNode = null;
let gardenLabelsVisible = true;

// Notes in the same category start near a shared anchor point on a ring,
// then physics (real edges + repulsion) takes over from there. Cheaper and
// far less fragile than vis-network's clustering API - which would merge
// nodes into meta-nodes and complicate every other feature below (click
// handling, neighbourhood highlight, search) - while still producing
// visible category neighbourhoods for a garden this size.
const GARDEN_CATEGORY_ORDER = ['AI', 'Cybersecurity', 'Software Engineering', 'Operating Systems', 'Research'];
const GARDEN_LABEL_ZOOM_THRESHOLD = 0.8;
const GARDEN_NODE_DIM_OPACITY = 0.12;
const GARDEN_EDGE_DIM_OPACITY = 0.08;

function themeColor(varName, fallback) {
    const value = getComputedStyle(document.documentElement).getPropertyValue(varName).trim();
    return value || fallback;
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
            // Pinned notes get a star shape and a heavier border so they
            // read as pinned at a glance, not just via the side panel.
            shape: n.is_pinned ? 'star' : 'dot',
            borderWidth: n.is_pinned ? 4 : 2,
            borderWidthSelected: n.is_pinned ? 5 : 3
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

    const edgeBaseColor = themeColor('--border-color', '#ccc');
    const edgeHighlightColor = themeColor('--primary-color', '#3f6b4f');
    const edgeHoverColor = themeColor('--text-secondary', '#666');

    const options = {
        nodes: {
            shape: 'dot',
            size: 20,
            font: {
                size: 12,
                color: themeColor('--text-primary', '#23281f'),
                face: 'Inter, sans-serif'
            },
            borderWidth: 2,
            shadow: true
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
        color: connected.has(node.id) ? node.color : hexToRgba(node.color, GARDEN_NODE_DIM_OPACITY)
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
            document.getElementById('panelCategory').textContent = note.category || 'Uncategorized';
            document.getElementById('panelDate').textContent = new Date(note.created_at).toLocaleDateString();
            document.getElementById('panelPreview').textContent = note.content.substring(0, 200) + (note.content.length > 200 ? '...' : '');
            
            const tagsContainer = document.getElementById('panelTags');
            tagsContainer.innerHTML = note.tags.map(tag => 
                `<span class="badge bg-light text-dark me-1">${tag}</span>`
            ).join('');
            
            const connectionsContainer = document.getElementById('panelConnections');
            if (note.connections.length > 0) {
                connectionsContainer.innerHTML = note.connections.map(conn => `
                    <div class="connection-item" onclick="showNotePanel(${conn.id})">
                        <div class="d-flex justify-content-between align-items-center">
                            <strong>${conn.title.substring(0, 30)}${conn.title.length > 30 ? '...' : ''}</strong>
                            <span class="badge bg-${conn.similarity > 0.8 ? 'success' : conn.similarity > 0.7 ? 'primary' : 'secondary'}">
                                ${(conn.similarity * 100).toFixed(0)}%
                            </span>
                        </div>
                        <small class="text-muted">${conn.category || 'Uncategorized'}</small>
                    </div>
                `).join('');
            } else {
                connectionsContainer.innerHTML = '<p class="text-muted small">No connections found</p>';
            }
            
            document.getElementById('panelViewBtn').href = `/notes/${note.id}`;
            selectedNode = nodeId;
        })
        .catch(error => console.error('Error loading note:', error));
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
            font: {
                size: 12,
                color: themeColor('--text-primary', '#23281f'),
                face: 'Inter, sans-serif'
            },
            borderWidth: 2,
            shadow: true
        },
        edges: {
            smooth: {
                type: 'continuous',
                roundness: 0.5
            },
            color: {
                color: themeColor('--border-color', '#ccc'),
                highlight: themeColor('--primary-color', '#3f6b4f'),
                hover: themeColor('--text-secondary', '#666')
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
    
    new vis.Network(container, dataset, options);
}

function initDarkMode() {
    const toggle = document.getElementById('darkModeToggle');
    const icon = document.getElementById('darkModeIcon');
    const html = document.documentElement;
    
    const savedMode = localStorage.getItem('darkMode');
    if (savedMode === 'true') {
        html.setAttribute('data-bs-theme', 'dark');
        if (icon) icon.className = 'bi bi-sun';
    }
    
    if (toggle) {
        toggle.addEventListener('click', function() {
            const isDark = html.getAttribute('data-bs-theme') === 'dark';
            html.setAttribute('data-bs-theme', isDark ? 'light' : 'dark');
            localStorage.setItem('darkMode', !isDark);
            if (icon) icon.className = isDark ? 'bi bi-moon' : 'bi bi-sun';
        });
    }
}

document.addEventListener('DOMContentLoaded', function() {
    initDarkMode();
    
    if (document.getElementById('gardenGraph')) {
        initGarden();
    }
    
    if (document.getElementById('focusGraph')) {
        initFocusGraph();
    }
    
    const physicsToggle = document.getElementById('physicsToggle');
    if (physicsToggle) {
        physicsToggle.addEventListener('change', togglePhysics);
    }

    document.querySelectorAll('.garden-category-filter').forEach(function(checkbox) {
        checkbox.addEventListener('change', applyGardenCategoryFilters);
    });

    setTimeout(function() {
        const flashMessages = document.getElementById('flashMessages');
        if (flashMessages) {
            flashMessages.style.transition = 'opacity 0.5s';
            flashMessages.style.opacity = '0';
            setTimeout(() => flashMessages.remove(), 500);
        }
    }, 5000);

    // Loading state for forms that trigger AI analysis (note create/edit,
    // document import). These block on server-side relationship scoring
    // (and, for the first search after startup, full embedding
    // generation) with no prior visual feedback - the page just appeared
    // to hang. Any form tagged data-ai-processing shows a spinner on its
    // submit button and disables it, so a slow save/import reads as
    // "working" rather than "broken". The disabled attribute also guards
    // against duplicate submits from an impatient double-click.
    document.querySelectorAll('form[data-ai-processing]').forEach(function(form) {
        form.addEventListener('submit', function() {
            if (form.dataset.aiProcessingSubmitted) return;
            form.dataset.aiProcessingSubmitted = 'true';

            const submitBtn = form.querySelector('button[type="submit"], input[type="submit"]');
            if (!submitBtn) return;

            const loadingText = submitBtn.dataset.loadingText || 'Processing...';
            submitBtn.disabled = true;

            if (submitBtn.tagName === 'BUTTON') {
                submitBtn.dataset.originalHtml = submitBtn.innerHTML;
                submitBtn.innerHTML =
                    '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>' +
                    loadingText;
            } else {
                submitBtn.dataset.originalValue = submitBtn.value;
                submitBtn.value = loadingText;
            }
        });
    });
});

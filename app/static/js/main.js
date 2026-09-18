let gardenNetwork = null;
let gardenNodesDataSet = null;
let allNodes = [];
let allEdges = [];
let selectedNode = null;

function themeColor(varName, fallback) {
    const value = getComputedStyle(document.documentElement).getPropertyValue(varName).trim();
    return value || fallback;
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
                color: themeColor('--border-color', '#ccc'),
                highlight: themeColor('--primary-color', '#3f6b4f'),
                hover: themeColor('--text-secondary', '#666'),
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

    gardenNodesDataSet = new vis.DataSet(nodes);
    const dataset = {
        nodes: gardenNodesDataSet,
        edges: new vis.DataSet(edges)
    };

    gardenNetwork = new vis.Network(container, dataset, options);

    gardenNetwork.on('click', function(params) {
        if (params.nodes.length > 0) {
            const nodeId = params.nodes[0];
            showNotePanel(nodeId);
        } else {
            closePanel();
        }
    });
    
    gardenNetwork.on('hoverNode', function(params) {
        container.style.cursor = 'pointer';
    });
    
    gardenNetwork.on('blurNode', function(params) {
        container.style.cursor = 'default';
    });
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
    const query = document.getElementById('searchNode').value.toLowerCase();
    if (!query) {
        gardenNetwork.selectNodes([]);
        return;
    }
    
    const matchingNodes = allNodes.filter(node => 
        node.label.toLowerCase().includes(query) || 
        node.title.toLowerCase().includes(query)
    );
    
    if (matchingNodes.length > 0) {
        gardenNetwork.selectNodes([matchingNodes[0].id]);
        gardenNetwork.focus(matchingNodes[0].id, {scale: 1.5, animation: true});
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
    
    fetch(`/garden/focus/${noteId}?depth=${depth}&min_similarity=${minSimilarity}`)
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

// The Knowledge Garden as a Streamlit component (tg_ui/static/index.html).
//
// Speaks Streamlit's component protocol directly (the same postMessage
// messages streamlit-component-lib sends), so the port needs no npm build.
// On the first render it receives the garden markup (rendered by Python
// from tg_ui/templates/tg/garden.html), the category list and the graph
// data, then loads vis-network, tg-core.js and garden-graph.js - the very
// files the Flask garden page runs - and boots the garden with a host that
// reads inline data and sends "open/edit/focus/create" back to Python.

(function () {
    'use strict';

    const DESKTOP_MIN_WIDTH = 992;
    let booted = false;
    let renderKey = null;
    let args = {};

    function send(type, data) {
        window.parent.postMessage(Object.assign({ isStreamlitMessage: true, type: type }, data), '*');
    }

    function setHeight() {
        const desktop = window.innerWidth >= DESKTOP_MIN_WIDTH;
        const height = desktop ? args.frame_height : document.documentElement.scrollHeight;
        send('streamlit:setFrameHeight', { height: Math.ceil(height) });
    }

    function loadScript(src) {
        return new Promise(function (resolve, reject) {
            const script = document.createElement('script');
            script.src = src;
            script.onload = resolve;
            script.onerror = function () { reject(new Error('Could not load ' + src)); };
            document.body.appendChild(script);
        });
    }

    function boot() {
        document.documentElement.style.setProperty('--embed-height', args.frame_height + 'px');
        // Server-rendered (autoescaped Jinja) markup from the shared template.
        document.getElementById('gardenRoot').innerHTML = args.markup;
        document.getElementById('gardenCategories').textContent = JSON.stringify(args.categories || []);

        const notes = args.notes || {};
        return loadScript('vendor/vis-network/9.1.9/vis-network.min.js')
            .then(function () { return loadScript('js/tg-core.js'); })
            .then(function () { return loadScript('js/garden-graph.js'); })
            .then(function () {
                configureGarden({
                    loadGraph: function () { return Promise.resolve({ nodes: args.nodes || [], edges: args.edges || [] }); },
                    loadNote: function (id) {
                        const note = notes[id];
                        return note ? Promise.resolve(note) : Promise.reject(new Error('Unknown note ' + id));
                    },
                    asset: function (path) { return path; },
                    links: { open: null, edit: null, focus: null },
                    navigate: function (action, id) {
                        send('streamlit:setComponentValue', {
                            value: { action: action, id: id, nonce: Date.now() },
                            dataType: 'json'
                        });
                    }
                });
                bootGarden();
                booted = true;
                setHeight();
            });
    }

    window.addEventListener('message', function (event) {
        const data = event.data || {};
        if (data.type !== 'streamlit:render') return;
        const next = data.args || {};
        if (booted && next.render_key === renderKey) {
            args = next;
            setHeight();
            return;
        }
        if (booted) {
            // New data (a note changed, another view): start from a clean page.
            window.location.reload();
            return;
        }
        args = next;
        renderKey = next.render_key;
        boot().catch(function (error) {
            console.error(error);
            document.getElementById('gardenRoot').textContent = 'The garden could not load.';
            setHeight();
        });
    });

    window.addEventListener('resize', function () {
        if (booted) setHeight();
    });
    if (window.ResizeObserver) {
        new ResizeObserver(function () {
            if (booted && window.innerWidth < DESKTOP_MIN_WIDTH) setHeight();
        }).observe(document.documentElement);
    }

    send('streamlit:componentReady', { apiVersion: 1 });
})();

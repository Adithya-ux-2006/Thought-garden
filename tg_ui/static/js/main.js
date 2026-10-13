// Flask page behaviour. Loads after tg-core.js on every page; garden pages
// also load vis-network and garden-graph.js (the graph code shared with the
// Streamlit port) before this file.

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
                badge.textContent = categoryLabel(note.category);
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
            if (typeof refreshGardenTheme === 'function') refreshGardenTheme();
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
        // the chip editor (initTagInputs) re-renders from the real input
        tagsInput.dispatchEvent(new Event('input'));
        chip.remove();
        if (!region.querySelector('button')) region.replaceChildren();
        const entry = form.querySelector('.tg-tags-entry');
        (entry || tagsInput).focus();
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

// ---------------------------------------------------------------------------
// Pickers: every <select class="form-select"> becomes a botanical menu - a
// pill trigger and a floating list with grouping, flower/tag icons, search
// for longer lists and, where allowed, a "new category" entry. The native
// <select> stays in the form (hidden) and remains the source of truth: the
// picker only sets its value and fires `change`, so autosubmit filters,
// the library controls and WTForms all keep working unchanged. Without JS
// the plain select is what you get.
//
// data-picker-kind="category" | "tag"   icons + grouping
// data-picker-custom                    offer typed text as a new option
// data-tg-picker="off"                  leave this select alone
// ---------------------------------------------------------------------------

const PICKER_SEARCH_MIN_OPTIONS = 8;
let pickerSeq = 0;
let openPicker = null;

function pickerOptionIcon(kind, value) {
    if (!value) return null;
    if (kind === 'category') {
        const meta = GARDEN_CATEGORY_BY_VALUE[value];
        const flower = (meta && meta.flower) || 'wildflower';
        const img = tgEl('img', 'tg-picker-plant');
        img.src = `/static/img/plants/${flower}-tree.svg`;
        img.alt = '';
        img.width = 64;
        img.height = 64;
        return img;
    }
    if (kind === 'tag') return tgEl('span', 'tg-picker-hash', '#');
    return null;
}

function pickerGroup(kind, value) {
    if (kind !== 'category' || !value) return '';
    const meta = GARDEN_CATEGORY_BY_VALUE[value];
    return meta ? meta.group || '' : 'Your categories';
}

function closeOpenPicker(returnFocus = false) {
    if (openPicker) openPicker.close(returnFocus);
}

function enhanceSelect(select) {
    if (select.dataset.tgPicker === 'off' || select.dataset.tgPickerReady || select.multiple) return;
    select.dataset.tgPickerReady = '1';
    const kind = select.dataset.pickerKind || '';
    const allowCustom = select.hasAttribute('data-picker-custom');
    const id = `tgPicker${++pickerSeq}`;
    const label = select.getAttribute('aria-label')
        || (select.labels && select.labels[0] && select.labels[0].textContent.trim()) || 'Choose';

    const wrap = tgEl('div', `tg-picker${select.classList.contains('form-select-sm') ? ' tg-picker--sm' : ''}`);
    const trigger = tgEl('button', 'tg-picker-trigger');
    trigger.type = 'button';
    trigger.setAttribute('aria-haspopup', 'listbox');
    trigger.setAttribute('aria-expanded', 'false');
    trigger.setAttribute('aria-controls', `${id}-menu`);
    if (select.classList.contains('is-invalid')) trigger.classList.add('is-invalid');
    const valueBox = tgEl('span', 'tg-picker-value');
    const chevron = tgEl('i', 'bi bi-chevron-down tg-picker-chevron');
    chevron.setAttribute('aria-hidden', 'true');
    trigger.append(valueBox, chevron);
    // the original <label for=...> now names the trigger
    if (select.id) {
        select.labels && Array.from(select.labels).forEach(l => { l.htmlFor = `${id}-trigger`; });
        trigger.id = `${id}-trigger`;
    }

    select.hidden = true;
    select.setAttribute('aria-hidden', 'true');
    select.tabIndex = -1;
    select.parentNode.insertBefore(wrap, select);
    wrap.append(trigger, select);

    const menu = tgEl('div', 'tg-picker-menu');
    menu.id = `${id}-menu`;
    menu.hidden = true;
    const list = tgEl('ul', 'tg-picker-list');
    list.id = `${id}-list`;
    list.setAttribute('role', 'listbox');
    list.setAttribute('aria-label', label);
    list.tabIndex = -1;

    const useSearch = kind || allowCustom || select.options.length >= PICKER_SEARCH_MIN_OPTIONS;
    let search = null;
    if (useSearch) {
        const box = tgEl('div', 'tg-picker-search');
        const icon = tgEl('i', 'bi bi-search');
        icon.setAttribute('aria-hidden', 'true');
        search = tgEl('input');
        search.type = 'text';
        search.autocomplete = 'off';
        search.spellcheck = false;
        search.setAttribute('role', 'combobox');
        search.setAttribute('aria-controls', list.id);
        search.setAttribute('aria-expanded', 'true');
        search.setAttribute('aria-autocomplete', 'list');
        search.setAttribute('aria-label', `Search: ${label}`);
        search.placeholder = allowCustom ? 'Search or name a new one…'
            : kind === 'tag' ? 'Search tags…' : kind === 'category' ? 'Search categories…' : 'Search…';
        box.append(icon, search);
        menu.appendChild(box);
    }
    const empty = tgEl('p', 'tg-picker-empty', 'Nothing matches.');
    empty.hidden = true;
    menu.append(list, empty);
    document.body.appendChild(menu);

    let items = [];
    let active = -1;

    function syncTrigger() {
        const option = select.options[select.selectedIndex];
        const text = option ? option.textContent.trim() : '';
        valueBox.replaceChildren();
        const icon = pickerOptionIcon(kind, option && option.value);
        if (icon) valueBox.appendChild(icon);
        valueBox.appendChild(tgEl('span', 'tg-picker-text', text));
        trigger.classList.toggle('is-placeholder', !option || !option.value);
        trigger.setAttribute('aria-label', `${label}: ${text}`);
    }

    function build(filter = '') {
        const query = filter.trim().toLowerCase();
        list.replaceChildren();
        items = [];
        let group = null;
        let exact = false;
        Array.from(select.options).forEach((option, index) => {
            const text = option.textContent.trim();
            if (query && !text.toLowerCase().includes(query) && !option.value.toLowerCase().includes(query)) return;
            if (query && (text.toLowerCase() === query || option.value.toLowerCase() === query)) exact = true;
            const g = pickerGroup(kind, option.value);
            if (g && g !== group) {
                const header = tgEl('li', 'tg-picker-group', g);
                header.setAttribute('role', 'presentation');
                list.appendChild(header);
            }
            group = g || group;
            const item = tgEl('li', 'tg-picker-option');
            item.id = `${id}-opt-${index}`;
            item.setAttribute('role', 'option');
            item.setAttribute('aria-selected', String(index === select.selectedIndex));
            if (!option.value) item.classList.add('is-empty');
            const icon = pickerOptionIcon(kind, option.value);
            if (icon) item.appendChild(icon);
            item.appendChild(tgEl('span', 'tg-picker-label', text));
            const check = tgEl('i', 'bi bi-check2 tg-picker-check');
            check.setAttribute('aria-hidden', 'true');
            item.appendChild(check);
            item.addEventListener('click', () => choose(index));
            item.addEventListener('pointermove', () => setActive(items.indexOf(item), false));
            list.appendChild(item);
            items.push(item);
        });
        if (allowCustom && query && !exact) {
            const typed = filter.trim().slice(0, 50);
            const item = tgEl('li', 'tg-picker-option tg-picker-create');
            item.id = `${id}-create`;
            item.setAttribute('role', 'option');
            item.setAttribute('aria-selected', 'false');
            const plus = tgEl('i', 'bi bi-plus-lg');
            plus.setAttribute('aria-hidden', 'true');
            item.append(plus, tgEl('span', 'tg-picker-label', `New category “${typed}”`));
            item.addEventListener('click', () => createOption(typed));
            list.appendChild(item);
            items.push(item);
        }
        empty.hidden = items.length > 0;
        const selected = items.findIndex(i => i.getAttribute('aria-selected') === 'true');
        setActive(selected >= 0 && !query ? selected : (items.length ? 0 : -1), true);
    }

    function setActive(index, scroll) {
        items.forEach(i => i.classList.remove('is-active'));
        active = index;
        const target = search || list;
        if (index < 0 || !items[index]) {
            target.removeAttribute('aria-activedescendant');
            return;
        }
        items[index].classList.add('is-active');
        target.setAttribute('aria-activedescendant', items[index].id);
        if (scroll) items[index].scrollIntoView({ block: 'nearest' });
    }

    function createOption(text) {
        if (!text) return;
        let option = Array.from(select.options).find(o => o.value.toLowerCase() === text.toLowerCase());
        if (!option) {
            option = new Option(text, text);
            select.add(option);
        }
        choose(option.index);
    }

    function choose(index) {
        const changed = select.selectedIndex !== index;
        select.selectedIndex = index;
        syncTrigger();
        close(true);
        if (changed) select.dispatchEvent(new Event('change', { bubbles: true }));
    }

    function place() {
        const rect = trigger.getBoundingClientRect();
        const margin = 8;
        const width = Math.max(rect.width, 240);
        const below = window.innerHeight - rect.bottom - margin;
        const above = rect.top - margin;
        const openUp = below < 220 && above > below;
        menu.style.minWidth = `${Math.min(width, window.innerWidth - 2 * margin)}px`;
        menu.style.maxWidth = `${Math.min(Math.max(width, 320), window.innerWidth - 2 * margin)}px`;
        menu.style.left = `${Math.max(margin, Math.min(rect.left, window.innerWidth - margin - Math.max(width, 240)))}px`;
        menu.style.maxHeight = `${Math.max(160, Math.min(400, (openUp ? above : below) - 6))}px`;
        menu.style.top = openUp ? '' : `${rect.bottom + 6}px`;
        menu.style.bottom = openUp ? `${window.innerHeight - rect.top + 6}px` : '';
        menu.classList.toggle('is-up', openUp);
    }

    function open() {
        if (!menu.hidden) return;
        closeOpenPicker();
        const scope = trigger.closest('[data-bs-theme]');
        menu.setAttribute('data-bs-theme', scope ? scope.getAttribute('data-bs-theme') : 'light');
        if (search) search.value = '';
        build();
        menu.hidden = false;
        place();
        trigger.setAttribute('aria-expanded', 'true');
        wrap.classList.add('is-open');
        openPicker = { close, place };
        (search || list).focus({ preventScroll: true });
    }

    function close(returnFocus = false) {
        if (menu.hidden) return;
        menu.hidden = true;
        trigger.setAttribute('aria-expanded', 'false');
        wrap.classList.remove('is-open');
        if (openPicker && openPicker.close === close) openPicker = null;
        if (returnFocus) trigger.focus({ preventScroll: true });
    }

    function onKeys(e) {
        if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
            e.preventDefault();
            if (!items.length) return;
            const step = e.key === 'ArrowDown' ? 1 : -1;
            setActive((active + step + items.length) % items.length, true);
        } else if (e.key === 'Home' && !search) {
            e.preventDefault();
            setActive(0, true);
        } else if (e.key === 'End' && !search) {
            e.preventDefault();
            setActive(items.length - 1, true);
        } else if (e.key === 'Enter') {
            e.preventDefault();
            if (items[active]) items[active].click();
        } else if (e.key === 'Escape') {
            e.preventDefault();
            e.stopPropagation();
            close(true);
        } else if (e.key === 'Tab') {
            close(false);
        }
    }

    trigger.addEventListener('click', () => (menu.hidden ? open() : close(true)));
    trigger.addEventListener('keydown', e => {
        if (['ArrowDown', 'ArrowUp'].includes(e.key)) {
            e.preventDefault();
            open();
        }
    });
    menu.addEventListener('keydown', onKeys);
    if (search) search.addEventListener('input', () => build(search.value));
    // the select can also change underneath (form.reset(), other scripts)
    select.addEventListener('change', syncTrigger);
    if (select.form) select.form.addEventListener('reset', () => setTimeout(syncTrigger));
    syncTrigger();
}

function initPickers() {
    document.querySelectorAll('select.form-select').forEach(enhanceSelect);
    document.addEventListener('pointerdown', e => {
        if (!openPicker) return;
        if (e.target.closest('.tg-picker-menu, .tg-picker')) return;
        closeOpenPicker();
    });
    // the floating list follows its trigger through scrolling, resizing and
    // the on-screen keyboard opening (closing on those would shut it the
    // moment a phone's keyboard appears)
    let queued = false;
    const follow = () => {
        if (!openPicker || queued) return;
        queued = true;
        requestAnimationFrame(() => {
            queued = false;
            if (openPicker) openPicker.place();
        });
    };
    window.addEventListener('resize', follow);
    window.addEventListener('scroll', follow, { passive: true, capture: true });
}

// ---------------------------------------------------------------------------
// Tag fields: the comma-separated tags input becomes a row of #tag chips
// with an entry that suggests the user's existing tags as you type. The
// original input stays in the form (hidden) holding "a, b, c", so the
// server, the tag-suggestion button and validation see exactly what they
// always did. Enter or a comma adds, Backspace on an empty entry removes
// the last chip, and pasting a list adds every tag in it.
// ---------------------------------------------------------------------------

const TAG_MAX_LENGTH = 50;
const TAG_SUGGESTION_LIMIT = 6;

function readUserTags() {
    const el = document.getElementById('userTags');
    if (!el) return [];
    try {
        return JSON.parse(el.textContent) || [];
    } catch (e) {
        return [];
    }
}

function initTagInputs() {
    const known = readUserTags();
    document.querySelectorAll('input[data-tag-input]').forEach(function(input) {
        const field = tgEl('div', 'tg-tags-field');
        const chips = tgEl('ul', 'tg-tags-chips');
        chips.setAttribute('aria-label', 'Tags on this note');
        const entry = tgEl('input', 'tg-tags-entry');
        entry.type = 'text';
        entry.autocomplete = 'off';
        entry.placeholder = input.placeholder || 'Add a tag…';
        entry.setAttribute('aria-label', 'Add a tag');
        entry.setAttribute('role', 'combobox');
        entry.setAttribute('aria-expanded', 'false');
        entry.setAttribute('aria-autocomplete', 'list');
        if (input.id) {
            Array.from(input.labels || []).forEach(l => { l.htmlFor = `${input.id}-entry`; });
            entry.id = `${input.id}-entry`;
        }
        const suggest = tgEl('ul', 'tg-tags-suggest');
        suggest.id = `${input.id || 'tags'}-suggest`;
        suggest.setAttribute('role', 'listbox');
        suggest.hidden = true;
        entry.setAttribute('aria-controls', suggest.id);
        const status = tgEl('span', 'visually-hidden');
        status.setAttribute('aria-live', 'polite');

        input.hidden = true;
        input.parentNode.insertBefore(field, input);
        field.append(chips, entry, suggest, status, input);
        field.addEventListener('click', e => { if (e.target === field || e.target === chips) entry.focus(); });

        let active = -1;
        const tags = () => input.value.split(',').map(t => t.trim()).filter(Boolean);

        function write(list) {
            input.value = list.join(', ');
            render();
        }

        function render() {
            chips.replaceChildren(...tags().map(name => {
                const chip = tgEl('li', 'tag tg-tag-chip', name);
                const remove = tgEl('button', 'tg-tag-remove');
                remove.type = 'button';
                remove.setAttribute('aria-label', `Remove tag ${name}`);
                const x = tgEl('i', 'bi bi-x');
                x.setAttribute('aria-hidden', 'true');
                remove.appendChild(x);
                remove.addEventListener('click', () => {
                    write(tags().filter(t => t !== name));
                    status.textContent = `Removed ${name}`;
                    entry.focus();
                });
                chip.appendChild(remove);
                return chip;
            }));
        }

        function add(raw) {
            const list = tags();
            const added = [];
            raw.split(',').map(t => t.trim().slice(0, TAG_MAX_LENGTH)).filter(Boolean).forEach(name => {
                if (!list.some(t => t.toLowerCase() === name.toLowerCase())) {
                    list.push(name);
                    added.push(name);
                }
            });
            if (added.length) {
                write(list);
                status.textContent = `Added ${added.join(', ')}`;
            }
            entry.value = '';
            hideSuggestions();
        }

        function hideSuggestions() {
            suggest.hidden = true;
            entry.setAttribute('aria-expanded', 'false');
            entry.removeAttribute('aria-activedescendant');
            active = -1;
        }

        function showSuggestions() {
            const q = entry.value.trim().toLowerCase();
            const have = new Set(tags().map(t => t.toLowerCase()));
            const matches = q ? known.filter(t => t.toLowerCase().includes(q) && !have.has(t.toLowerCase()))
                .slice(0, TAG_SUGGESTION_LIMIT) : [];
            suggest.replaceChildren(...matches.map((name, i) => {
                const item = tgEl('li', 'tg-tags-option', name);
                item.id = `${suggest.id}-${i}`;
                item.setAttribute('role', 'option');
                item.addEventListener('pointerdown', e => { e.preventDefault(); add(name); });
                return item;
            }));
            suggest.hidden = matches.length === 0;
            entry.setAttribute('aria-expanded', String(!suggest.hidden));
            active = -1;
        }

        function move(step) {
            const options = Array.from(suggest.children);
            if (!options.length) return;
            active = (active + step + options.length) % options.length;
            options.forEach((o, i) => o.classList.toggle('is-active', i === active));
            entry.setAttribute('aria-activedescendant', options[active].id);
        }

        entry.addEventListener('keydown', e => {
            if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
                if (suggest.hidden) return;
                e.preventDefault();
                move(e.key === 'ArrowDown' ? 1 : -1);
            } else if (e.key === 'Enter' || e.key === ',') {
                const options = Array.from(suggest.children);
                if (e.key === 'Enter' && !suggest.hidden && options[active]) {
                    e.preventDefault();
                    add(options[active].textContent);
                } else if (entry.value.trim()) {
                    e.preventDefault();
                    add(entry.value);
                } else if (e.key === ',') {
                    e.preventDefault();
                }
            } else if (e.key === 'Backspace' && !entry.value) {
                const list = tags();
                if (list.length) {
                    const removed = list.pop();
                    write(list);
                    status.textContent = `Removed ${removed}`;
                }
            } else if (e.key === 'Escape' && !suggest.hidden) {
                e.preventDefault();
                hideSuggestions();
            }
        });
        entry.addEventListener('input', () => {
            if (entry.value.includes(',')) add(entry.value);
            else showSuggestions();
        });
        entry.addEventListener('blur', () => {
            if (entry.value.trim()) add(entry.value);
            hideSuggestions();
        });
        // other scripts (tag suggestions) write the real input directly
        input.addEventListener('input', render);
        render();
    });
}

document.addEventListener('DOMContentLoaded', function() {
    initConfirmForms();
    initDarkMode();
    initSearchAutocomplete();
    initTagSuggestions();
    initPickers();
    initTagInputs();

    if (typeof bootGarden === 'function') bootGarden();
    if (typeof initFocusGraph === 'function') initFocusGraph();

    document.querySelectorAll('select[data-autosubmit]').forEach(function(select) {
        select.addEventListener('change', () => select.form.submit());
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

// Helpers shared by every Thought Garden script: the Flask pages (main.js),
// the garden graph (garden-graph.js) and the Streamlit garden component.
// Classic script, top-level bindings - loaded before the others.

// Category order/slugs come from tg_ui/categories.py via a JSON data block
// (#gardenCategories), so the client list can't drift from the server's.
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
const GARDEN_CATEGORY_BY_VALUE = Object.fromEntries(GARDEN_CATEGORIES.map(c => [c.value, c]));
const WILD_CATEGORY_LABEL = 'Wild thoughts';

function prefersReducedMotion() {
    return Boolean(window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches);
}

function themeColor(varName, fallback, el = document.documentElement) {
    const value = getComputedStyle(el).getPropertyValue(varName).trim();
    return value || fallback;
}

function hexToRgb(hex) {
    const clean = hex.replace('#', '');
    const full = clean.length === 3 ? clean.split('').map(c => c + c).join('') : clean;
    const num = parseInt(full, 16);
    return `${(num >> 16) & 255}, ${(num >> 8) & 255}, ${num & 255}`;
}

function hexToRgba(hex, alpha) {
    return `rgba(${hexToRgb(hex)}, ${alpha})`;
}

function gardenCategorySlug(category) {
    const c = GARDEN_CATEGORY_BY_VALUE[category];
    return c ? c.slug : 'none';
}

function gardenCategoryBadgeClass(category) {
    return `badge-category-${gardenCategorySlug(category)}`;
}

// A missing category reads as "Wild thoughts" (the API still sends
// 'Uncategorized' / null; this is display only).
function categoryLabel(category) {
    return !category || category === 'Uncategorized' ? WILD_CATEGORY_LABEL : category;
}

// Readable text from Markdown for previews (mirrors tg_ui.presenters.plain_text).
function plainText(markdown) {
    return String(markdown || '')
        .replace(/```[\s\S]*?```/g, ' ')
        .replace(/!\[([^\]]*)\]\([^)]*\)/g, '$1')
        .replace(/\[([^\]]+)\]\([^)]*\)/g, '$1')
        .replace(/<[^>]+>/g, ' ')
        .replace(/^\s{0,3}(?:#{1,6}\s+|>\s?|[-*+]\s+|\d+[.)]\s+)/gm, '')
        .replace(/(\*\*|__|\*|_|~~|`)/g, '');
}

function readingMinutes(markdown) {
    const words = plainText(markdown).split(/\s+/).filter(Boolean).length;
    return Math.max(1, Math.ceil(words / 200));
}

// Small DOM builder for user content: text always goes in as textContent.
function tgEl(tag, className, text) {
    const el = document.createElement(tag);
    if (className) el.className = className;
    if (text !== undefined && text !== null) el.textContent = text;
    return el;
}

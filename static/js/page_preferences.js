/* Admin-only, scoped presentation settings. No business data is sent or changed. */
document.addEventListener('DOMContentLoaded', () => {
    const panel = document.querySelector('.page-personalization');
    const root = document.getElementById('pageContent') || document.getElementById('rete-container');
    if (!panel || !root) return;
    root.classList.add('page-customized');
    const theme = document.getElementById('pageTheme');
    const density = document.getElementById('pageDensity');
    const font = document.getElementById('pageFont');
    const container = document.getElementById('pageVisibilityControls');
    const visibility = [];
    const groups = new Map();
    root.querySelectorAll('[data-custom-section]').forEach(node => {
        const id = node.dataset.customSection;
        if (!groups.has(id)) groups.set(id, {label: node.dataset.customLabel || id, nodes: []});
        groups.get(id).nodes.push(node);
    });
    const addHeading = text => {
        const heading = document.createElement('h3'); heading.className = 'h6 mt-3 mb-2'; heading.textContent = text; container.append(heading);
    };
    const addControl = (key, label, nodes) => {
        const wrapper = document.createElement('label'); wrapper.className = 'page-visibility-option';
        const input = document.createElement('input'); input.type = 'checkbox'; input.checked = true; input.className = 'form-check-input'; input.dataset.preference = key;
        const text = document.createElement('span'); text.textContent = label;
        wrapper.append(input, text); container.append(wrapper);
        visibility.push({key, input, nodes});
    };
    if (groups.size) addHeading('Блоки');
    groups.forEach((group, id) => addControl('section:' + id, group.label, group.nodes));
    root.querySelectorAll('table:not(.portfolio-table)').forEach((table, index) => {
        const headers = [...(table.tHead?.rows[0]?.cells || [])];
        if (!headers.length) return;
        const pane = table.closest('.tab-pane');
        const label = pane ? document.getElementById(pane.id + '-tab')?.textContent.trim() : '';
        addHeading('Стовпці' + (label ? ': ' + label : ' · ' + (index + 1)));
        headers.forEach((header, column) => {
            const text = header.textContent.trim();
            // Keep titles and action links available, even when optional columns are hidden.
            if (!text || /назв|назван|title|дії|действ|action/i.test(text)) return;
            if (column === 0 && [...table.tBodies].some(body => [...body.rows].some(row => row.cells[0]?.querySelector('a')))) return;
            const nodes = [...table.rows].map(row => row.cells[column]).filter(cell => cell && cell.colSpan === 1);
            addControl('table:' + index + ':column:' + column, text, nodes);
        });
    });
    const params = new URLSearchParams(location.search);
    let mode = params.get('mode') || '1';
    let state = {};
    const key = () => 'uvp-admin-page:' + panel.dataset.user + ':' + panel.dataset.route + ':' + location.pathname.replace(/\d+/g, ':id') + ':mode:' + mode;
    const apply = () => {
        root.dataset.pageTheme = theme.value;
        root.dataset.pageDensity = density.value;
        root.dataset.pageFont = font.value;
        visibility.forEach(control => control.nodes.forEach(node => node.classList.toggle('page-pref-hidden', !control.input.checked)));
        if (root.id === 'rete-container' && typeof viz !== 'undefined' && typeof viz.render === 'function') viz.render();
        if (typeof window.Chart?.getChart === 'function') {
            const color = getComputedStyle(root).color;
            root.querySelectorAll('canvas').forEach(canvas => {
                const chart = window.Chart.getChart(canvas);
                if (!chart) return;
                chart.options.color = color;
                if (chart.options.plugins?.legend?.labels) chart.options.plugins.legend.labels.color = color;
                Object.values(chart.options.scales || {}).forEach(scale => { if (scale.ticks) scale.ticks.color = color; });
                chart.update('none');
            });
        }
    };
    const valid = (select, value, fallback) => [...select.options].some(option => option.value === value) ? value : fallback;
    const load = () => {
        try { state = JSON.parse(localStorage.getItem(key()) || '{}') || {}; } catch (_) { state = {}; }
        if (typeof state !== 'object' || Array.isArray(state)) state = {};
        theme.value = valid(theme, state.theme, 'default'); density.value = valid(density, state.density, 'comfortable'); font.value = valid(font, state.font, 'normal');
        visibility.forEach(control => { control.input.checked = state.hidden?.[control.key] !== true; });
        apply();
    };
    const save = () => {
        state = {theme: theme.value, density: density.value, font: font.value, hidden: {}};
        visibility.forEach(control => { if (!control.input.checked) state.hidden[control.key] = true; });
        apply(); try { localStorage.setItem(key(), JSON.stringify(state)); } catch (_) {}
    };
    [theme, density, font, ...visibility.map(control => control.input)].forEach(input => input.addEventListener('change', save));
    document.getElementById('resetPagePreferences').addEventListener('click', () => { try { localStorage.removeItem(key()); } catch (_) {} load(); });
    document.querySelector('.uvp-mode-switch')?.addEventListener('uvp-mode-change', event => { mode = event.detail.mode; load(); });
    document.addEventListener('click', event => { if (!panel.contains(event.target)) document.getElementById('pagePreferences').open = false; });
    document.addEventListener('keydown', event => { if (event.key === 'Escape') document.getElementById('pagePreferences').open = false; });
    if (root.id === 'rete-container') {
        const toolbar = document.getElementById('toolbar');
        if (toolbar && window.ResizeObserver) new ResizeObserver(() => { root.style.setProperty('top', toolbar.offsetHeight + 'px', 'important'); }).observe(toolbar);
    }
    load();
});

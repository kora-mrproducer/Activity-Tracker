// Common JavaScript - Activity Tracker
// Shared utilities and global functions

// ================== Font Size Management ==================

(function(){
    const LS_KEY = 'tracker.fontSize';
    const root = document.documentElement;
    const minPx = 9, maxPx = 18; // allow some range
    
    function apply(px){ 
        root.style.setProperty('--base-font-size', px + 'px'); 
        const v = document.getElementById('fontValue'); 
        if(v) v.textContent = px + 'px'; 
    }
    
    function load(){ 
        const saved = parseInt(localStorage.getItem(LS_KEY), 10); 
        if(saved && saved >= minPx && saved <= maxPx){ 
            apply(saved);
        } else { 
            apply(11); 
        } 
    }
    
    function save(px){ 
        localStorage.setItem(LS_KEY, px); 
    }
    
    function adjust(delta){ 
        const cur = parseInt(getComputedStyle(root).getPropertyValue('--base-font-size')); 
        const next = Math.min(maxPx, Math.max(minPx, cur + delta)); 
        apply(next); 
        save(next); 
        showToast('Font size: ' + next + 'px', 'info', 1200); 
    }
    
    window.resetFont = function(){ 
        apply(11); 
        save(11); 
        showToast('Font size reset', 'info', 1200); 
    };
    
    window.incFont = function(){ 
        adjust(1); 
    };
    
    window.decFont = function(){ 
        adjust(-1); 
    };
    
    document.addEventListener('DOMContentLoaded', ()=>{
        // ===== Theme (light/dark) =====
        const THEME_KEY = 'tracker.theme';
        const prefersLight = window.matchMedia && window.matchMedia('(prefers-color-scheme: light)').matches;
        function applyTheme(theme){
            // apply to root early-applied class as well as body for compatibility
            document.documentElement.classList.toggle('theme-light', theme === 'light');
            document.body.classList.toggle('theme-light', theme === 'light');
            const icon = document.getElementById('themeIcon');
            const btn = document.getElementById('themeToggle');
            // Show icon for NEXT theme (moon when light active, sun when dark active)
            if(icon){
                if(theme === 'light'){ icon.classList.remove('fa-sun'); icon.classList.add('fa-moon'); }
                else { icon.classList.remove('fa-moon'); icon.classList.add('fa-sun'); }
            }
            if(btn){ btn.setAttribute('aria-label', theme === 'light' ? 'Switch to dark mode' : 'Switch to light mode'); }
        }
        function currentTheme(){ return localStorage.getItem(THEME_KEY) || (prefersLight ? 'light' : 'dark'); }
        applyTheme(currentTheme());
        const toggleBtn = document.getElementById('themeToggle');
        if(toggleBtn){
            toggleBtn.addEventListener('click', ()=>{
                // Add transition class temporarily
                document.body.classList.add('theme-transition');
                const next = (currentTheme() === 'light') ? 'dark' : 'light';
                localStorage.setItem(THEME_KEY, next);
                applyTheme(next);
                if(typeof showToast === 'function') showToast(next === 'light' ? 'Light mode' : 'Dark mode', 'info', 1100);
                setTimeout(()=> document.body.classList.remove('theme-transition'), 600);
            });
        }
        load();
        const dec = document.getElementById('fontDec');
        const inc = document.getElementById('fontInc');
        const rst = document.getElementById('fontReset');
        if(dec) dec.addEventListener('click', decFont);
        if(inc) inc.addEventListener('click', incFont);
        if(rst) rst.addEventListener('click', resetFont);
        
        // Settings panel toggle
        const settingsToggle = document.getElementById('settingsToggle');
        const settingsPanel = document.getElementById('settingsPanel');
        const settingsChevron = document.getElementById('settingsChevron');
        if(settingsToggle && settingsPanel){
            settingsToggle.addEventListener('click', function(){
                settingsPanel.classList.toggle('hidden');
                if(settingsChevron) {
                    settingsChevron.style.transform = settingsPanel.classList.contains('hidden') 
                        ? 'rotate(0deg)' 
                        : 'rotate(180deg)';
                }
            });
        }
        
        // Density toggle
        const densitySelect = document.getElementById('densitySelect');
        const savedDensity = localStorage.getItem('tracker.density') || 'comfortable';
        if(densitySelect){
            densitySelect.value = savedDensity;
            document.body.classList.toggle('compact', savedDensity === 'compact');
            densitySelect.addEventListener('change', function(){
                const val = this.value;
                localStorage.setItem('tracker.density', val);
                document.body.classList.toggle('compact', val === 'compact');
                if(typeof showToast === 'function') showToast('Density: ' + val, 'info', 1200);
            });
        }
        
        // Column visibility toggle
        const colToggles = document.querySelectorAll('.col-toggle');
        const savedCols = JSON.parse(localStorage.getItem('tracker.columns') || 
            '{"source":true,"start_date":true,"blocking_points":true}');
        colToggles.forEach(function(toggle){
            const col = toggle.getAttribute('data-col');
            toggle.checked = savedCols[col] !== false;
            applyColumnVisibility(col, toggle.checked);
            toggle.addEventListener('change', function(){
                savedCols[col] = this.checked;
                localStorage.setItem('tracker.columns', JSON.stringify(savedCols));
                applyColumnVisibility(col, this.checked);
            });
        });
        
        function applyColumnVisibility(col, visible){
            const cls = 'col-' + col;
            const els = document.querySelectorAll('.' + cls);
            els.forEach(function(el){ 
                el.style.display = visible ? '' : 'none'; 
            });
        }
    });
})();

// ================== Toast System ==================

window.showToast = function(msg, type='info', ttl=2500){
    const wrap = document.getElementById('toast-container'); 
    if(!wrap) return;
    
    wrap.setAttribute('aria-live', 'polite');
    wrap.setAttribute('aria-atomic', 'true');
    
    // Icon based on type
    let icon = 'fa-info-circle';
    if (type === 'success') icon = 'fa-check-circle';
    else if (type === 'error') icon = 'fa-exclamation-circle';
    
    const d = document.createElement('div'); 
    d.className = 'toast toast-' + (type || 'info');
    d.setAttribute('role', 'status');
    d.innerHTML = `
        <i class="fas ${icon}" style="font-size: 18px;"></i>
        <span style="flex: 1;">${msg}</span>
        <button onclick="this.parentElement.classList.add('toast-removing'); setTimeout(() => this.parentElement.remove(), 300);" aria-label="Dismiss">
            <i class='fas fa-times' style="font-size: 12px;"></i>
        </button>
    `;
    
    wrap.appendChild(d);
    
    setTimeout(()=> { 
        d.classList.add('toast-removing');
        setTimeout(() => d.remove(), 300); 
    }, ttl);
};

// ================== Flash Messages ==================

document.addEventListener('DOMContentLoaded', function(){
    const flashes = document.querySelectorAll('#flash-messages > div');
    flashes.forEach(function(flash){
        const cat = flash.getAttribute('data-category');
        const msg = flash.getAttribute('data-message');
        const type = (cat === 'success') ? 'success' : (cat === 'error') ? 'error' : 'info';
        if(typeof showToast === 'function') showToast(msg, type, 3000);
    });
});

// ================== Global Keyboard Shortcuts ==================

document.addEventListener('keydown', function(e){
    // Show help on ?
    if(e.key === '?' && !e.ctrlKey && !e.shiftKey && 
       !['INPUT','TEXTAREA','SELECT'].includes(e.target.tagName)){
        e.preventDefault();
        const helpOverlay = document.getElementById('helpOverlay');
        if(helpOverlay) helpOverlay.style.display = 'flex';
        return;
    }
    
    // Open search on /
    if(e.key === '/' && !e.ctrlKey && !e.shiftKey && 
       !['INPUT','TEXTAREA','SELECT'].includes(e.target.tagName)){
        e.preventDefault();
        openSearch();
        return;
    }
    
    // Close help/modals on Escape
    if(e.key === 'Escape'){
        const help = document.getElementById('helpOverlay');
        if(help && help.style.display !== 'none'){
            help.style.display = 'none';
            return;
        }
        const search = document.getElementById('searchModal');
        if(search && search.style.display !== 'none'){
            closeSearch();
            return;
        }
    }
});

// ================== Search Functionality ==================

let searchTimeout = null;

function openSearch() {
    const modal = document.getElementById('searchModal');
    const input = document.getElementById('searchInput');
    if (modal && input) {
        modal.style.display = 'flex';
        setTimeout(() => input.focus(), 100);
    }
}

function closeSearch() {
    const modal = document.getElementById('searchModal');
    const input = document.getElementById('searchInput');
    const results = document.getElementById('searchResults');
    if (modal) modal.style.display = 'none';
    if (input) input.value = '';
    if (results) {
        results.innerHTML = `
            <div class="text-center py-8 text-secondary">
                <i class="fas fa-search text-4xl mb-2 opacity-50"></i>
                <p>Type to search activities...</p>
            </div>
        `;
    }
}

// Search input handler
document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('searchInput');
    if (!searchInput) return;
    
    searchInput.addEventListener('input', function(e) {
        const query = e.target.value.trim();
        
        // Clear previous timeout
        if (searchTimeout) clearTimeout(searchTimeout);
        
        if (query.length < 2) {
            document.getElementById('searchResults').innerHTML = `
                <div class="text-center py-8 text-secondary">
                    <i class="fas fa-search text-4xl mb-2 opacity-50"></i>
                    <p>Type at least 2 characters to search...</p>
                </div>
            `;
            return;
        }
        
        // Show loading
        document.getElementById('searchResults').innerHTML = `
            <div class="text-center py-8 text-secondary">
                <i class="fas fa-spinner fa-spin text-4xl mb-2"></i>
                <p>Searching...</p>
            </div>
        `;
        
        // Debounce search (wait 300ms after user stops typing)
        searchTimeout = setTimeout(() => {
            fetch('/search?q=' + encodeURIComponent(query))
                .then(r => r.json())
                .then(results => {
                    displaySearchResults(results);
                })
                .catch(err => {
                    console.error('Search error:', err);
                    document.getElementById('searchResults').innerHTML = `
                        <div class="text-center py-8" style="color: var(--md-sys-color-error);">
                            <i class="fas fa-exclamation-circle text-4xl mb-2"></i>
                            <p>Search failed. Please try again.</p>
                        </div>
                    `;
                });
        }, 300);
    });
    
    // Navigate results with arrow keys
    searchInput.addEventListener('keydown', function(e) {
        if (e.key === 'ArrowDown') {
            e.preventDefault();
            const first = document.querySelector('.search-result-item');
            if (first) first.focus();
        }
    });
});

function displaySearchResults(results) {
    const container = document.getElementById('searchResults');
    if (!results || results.length === 0) {
        container.innerHTML = `
            <div class="text-center py-8 text-secondary">
                <i class="fas fa-inbox text-4xl mb-2 opacity-50"></i>
                <p>No activities found matching your search.</p>
            </div>
        `;
        return;
    }
    
    const priorityColors = {
        'High': 'var(--md-sys-color-error)',
        'Medium': '#f59e0b',
        'Low': '#10b981'
    };
    
    const statusBadges = {
        'Ongoing': '<span class="px-2 py-1 rounded text-xs" style="background: #3b82f6; color: white;">Ongoing</span>',
        'Closed': '<span class="px-2 py-1 rounded text-xs" style="background: #10b981; color: white;">Closed</span>',
        'NA': '<span class="px-2 py-1 rounded text-xs" style="background: #6b7280; color: white;">N/A</span>'
    };
    
    container.innerHTML = results.map((r, index) => `
        <a href="/activity/${r.id}" 
           class="search-result-item block p-4 rounded-lg hover:bg-opacity-80 transition focus:outline-none focus:ring-2"
           style="background: var(--md-sys-color-surface-container); border-left: 4px solid ${priorityColors[r.priority] || '#6b7280'};"
           tabindex="0"
           onkeydown="if(event.key==='ArrowDown'&&event.target.nextElementSibling) {event.preventDefault(); event.target.nextElementSibling.focus();} else if(event.key==='ArrowUp'&&event.target.previousElementSibling) {event.preventDefault(); event.target.previousElementSibling.focus();} else if(event.key==='Enter') {window.location.href='/activity/${r.id}';}">
            <div class="flex items-start gap-3">
                <div class="flex-1">
                    <div class="flex items-center gap-2 mb-1">
                        <span class="font-semibold" style="color: var(--md-sys-color-on-surface);">${r.desc}</span>
                    </div>
                    <div class="flex items-center gap-2 text-sm flex-wrap">
                        ${statusBadges[r.status] || ''}
                        <span class="px-2 py-1 rounded text-xs" style="background: var(--md-sys-color-surface-container-highest); color: var(--md-sys-color-on-surface-variant);">
                            ${r.priority}
                        </span>
                        ${r.source ? `<span style="color: var(--md-sys-color-on-surface-variant);">${r.source}</span>` : ''}
                        ${r.start_date ? `<span style="color: var(--md-sys-color-on-surface-variant);"><i class="fas fa-calendar-alt mr-1"></i>${r.start_date}</span>` : ''}
                    </div>
                </div>
                <i class="fas fa-arrow-right" style="color: var(--md-sys-color-on-surface-variant);"></i>
            </div>
        </a>
    `).join('');
}


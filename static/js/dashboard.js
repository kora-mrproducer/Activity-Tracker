// Dashboard JavaScript - Activity Tracker
// Extracted from inline scripts for better maintainability

// Debug flag - set to true during development only
const DEBUG = false;

function debugLog(...args) {
    if (DEBUG && typeof console !== 'undefined') {
        console.log(...args);
    }
}

// ================== UI Controls ==================

function toggleGoalForm() {
    const form = document.getElementById('goalForm');
    form.classList.toggle('hidden');
}

function togglePrioritySection(priority) {
    const content = document.getElementById('content-' + priority);
    const chevron = document.getElementById('chevron-' + priority);
    if(content.style.display === 'none'){
        content.style.display = 'block';
        if(chevron) chevron.style.transform = 'rotate(180deg)';
    } else {
        content.style.display = 'none';
        if(chevron) chevron.style.transform = 'rotate(0deg)';
    }
}

// Action menu toggle
function toggleActionMenu(activityId) {
    const menu = document.getElementById('actionMenu' + activityId);
    // Close all other menus
    document.querySelectorAll('[id^="actionMenu"]').forEach(m => {
        if (m.id !== 'actionMenu' + activityId) m.classList.add('hidden');
    });
    menu.classList.toggle('hidden');
}

// Close action menus when clicking outside
document.addEventListener('click', function(e) {
    if (!e.target.closest('[id^="actionMenu"]') && !e.target.closest('button[onclick^="toggleActionMenu"]')) {
        document.querySelectorAll('[id^="actionMenu"]').forEach(m => m.classList.add('hidden'));
    }
});

// Edit status inline
function editStatus(activityId, currentStatus) {
    document.getElementById('st_display_' + activityId).classList.add('hidden');
    document.getElementById('st_edit_' + activityId).classList.remove('hidden');
}

// ================== Update Modal ==================

function openUpdateModal(activityId, activityDesc, currentBP) {
    const modal = document.getElementById('updateModal');
    const form = document.getElementById('quickUpdateForm');
    const descElem = document.getElementById('modalActivityDesc');
    const textarea = document.getElementById('modalUpdateText');
    const bpArea = document.getElementById('modalBlockingPoints');
    
    descElem.textContent = activityDesc;
    form.action = `/activity/${activityId}/update`;
    textarea.value = '';
    if (bpArea) bpArea.value = currentBP || '';
    modal.classList.remove('hidden');
    textarea.focus();
}

function closeUpdateModal() {
    const modal = document.getElementById('updateModal');
    modal.classList.add('hidden');
}

// ================== Closing Note Modal ==================

let pendingCloseActivityId = null;

function openClosingNoteModal(activityId) {
    pendingCloseActivityId = activityId;
    const modal = document.getElementById('closingNoteModal');
    const textarea = document.getElementById('closingNoteText');
    textarea.value = '';
    modal.classList.remove('hidden');
    textarea.focus();
}

function closeClosingNoteModal() {
    const modal = document.getElementById('closingNoteModal');
    modal.classList.add('hidden');
    
    // Revert the status dropdown if cancelled
    if (pendingCloseActivityId) {
        cancelStatus(pendingCloseActivityId);
    }
    
    pendingCloseActivityId = null;
}

async function confirmClosingNote() {
    const closingNote = document.getElementById('closingNoteText').value.trim();
    if (!closingNote) {
        if (typeof showToast === 'function') {
            showToast('Please provide a closing note', 'error');
        }
        return;
    }
    
    if (!pendingCloseActivityId) return;
    
    const id = pendingCloseActivityId;
    closeClosingNoteModal();
    
    const statusEl = document.getElementById(`st_status_${id}`);
    if (statusEl) {
        statusEl.textContent = 'Saving...';
        statusEl.classList.remove('hidden');
    }
    
    try {
        const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content;
        const headers = { 'Content-Type': 'application/json' };
        if (csrfToken) {
            headers['X-CSRFToken'] = csrfToken;
            headers['X-CSRF-Token'] = csrfToken;
        }
        
        const resp = await fetch(`/activity/${id}/status`, {
            method: 'POST',
            headers: headers,
            body: JSON.stringify({ 
                status: 'Closed',
                closing_note: closingNote
            })
        });
        const data = await resp.json();
        if (!resp.ok || !data.ok) throw new Error(data.error || 'Failed');
        
        const disp = document.getElementById(`st_display_${id}`);
        const edit = document.getElementById(`st_edit_${id}`);
        if (disp && edit) {
            disp.innerHTML = renderStatusBadge('Closed', id);
            edit.classList.add('hidden');
            disp.classList.remove('hidden');
        }
        if (statusEl) {
            statusEl.textContent = 'Saved';
            setTimeout(() => statusEl.classList.add('hidden'), 800);
        }
        if (typeof showToast === 'function') { 
            showToast('Activity closed successfully', 'success'); 
        }
    } catch (e) {
        if (statusEl) {
            statusEl.textContent = 'Error saving';
        }
        if (typeof showToast === 'function') { 
            showToast('Error closing activity', 'error'); 
        }
    }
}

// ================== Inline Status Editing ==================

function startEditStatus(id, current) {
    debugLog('startEditStatus called with id:', id, 'current:', current);
    const disp = document.getElementById(`st_display_${id}`);
    const edit = document.getElementById(`st_edit_${id}`);
    debugLog('Found elements - disp:', !!disp, 'edit:', !!edit);
    if (disp && edit) {
        disp.classList.add('hidden');
        edit.classList.remove('hidden');
        const sel = document.getElementById(`st_select_${id}`);
        if (sel) sel.value = current;
        debugLog('Status edit mode activated for activity', id);
    } else {
        debugLog('Error: Could not find status display or edit elements for activity', id);
    }
}

function cancelStatus(id) {
    const disp = document.getElementById(`st_display_${id}`);
    const edit = document.getElementById(`st_edit_${id}`);
    if (disp && edit) {
        edit.classList.add('hidden');
        disp.classList.remove('hidden');
    }
}

async function saveStatus(id) {
    const sel = document.getElementById(`st_select_${id}`);
    const statusEl = document.getElementById(`st_status_${id}`);
    if (!sel) return;
    const newVal = sel.value;
    
    // If changing to Closed, prompt for closing note
    if (newVal === 'Closed') {
        openClosingNoteModal(id);
        return;
    }
    
    if (statusEl) {
        statusEl.textContent = 'Saving...';
        statusEl.classList.remove('hidden');
    }
    try {
        const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content;
        const headers = { 'Content-Type': 'application/json' };
        if (csrfToken) {
            headers['X-CSRFToken'] = csrfToken;
            headers['X-CSRF-Token'] = csrfToken;
        }
        
        const resp = await fetch(`/activity/${id}/status`, {
            method: 'POST',
            headers: headers,
            body: JSON.stringify({ status: newVal })
        });
        const data = await resp.json();
        if (!resp.ok || !data.ok) throw new Error(data.error || 'Failed');
        const disp = document.getElementById(`st_display_${id}`);
        const edit = document.getElementById(`st_edit_${id}`);
        if (disp && edit) {
            disp.innerHTML = renderStatusBadge(newVal, id);
            edit.classList.add('hidden');
            disp.classList.remove('hidden');
        }
        if (statusEl) {
            statusEl.textContent = 'Saved';
            setTimeout(() => statusEl.classList.add('hidden'), 800);
        }
        if (typeof showToast === 'function') { showToast('Status updated', 'success'); }
    } catch (e) {
        if (statusEl) {
            statusEl.textContent = 'Error saving';
        }
        if (typeof showToast === 'function') { showToast('Error updating status', 'error'); }
    }
}

function renderStatusBadge(val, id) {
    const statusConfig = {
        'Ongoing': {icon: 'fa-spinner', bg: 'bg-yellow-900/30', text: 'text-yellow-400', border: 'border-yellow-600'},
        'Closed': {icon: 'fa-check', bg: 'bg-green-900/30', text: 'text-green-400', border: 'border-green-600'},
        'NA': {icon: '', bg: 'bg-gray-700', text: 'text-gray-300', border: 'border-gray-600'}
    };
    const config = statusConfig[val] || statusConfig['NA'];
    const iconHtml = config.icon ? `<i class='fas ${config.icon} mr-1.5'></i>` : '';
    return `<span class="inline-flex items-center px-3 py-1.5 text-xs font-medium ${config.bg} ${config.text} rounded-full border ${config.border}">${iconHtml}${val}</span> <button class='md-icon-button !w-8 !h-8 edit-status-btn' title='Edit status' data-id='${id}' data-current='${val}'><i class='fas fa-pen text-xs'></i></button>`;
}

// ================== Column Sorting ==================

function toggleSort(col){
    const url = new URL(window.location);
    const currentSort = url.searchParams.get('sort');
    const currentDir = url.searchParams.get('dir') || 'asc';
    if(currentSort === col){
        url.searchParams.set('dir', currentDir === 'asc' ? 'desc' : 'asc');
    } else {
        url.searchParams.set('sort', col);
        url.searchParams.set('dir', 'asc');
    }
    window.location = url.toString();
}

// ================== Delete with Undo ==================

let deletedActivity = null;

function undoDelete(){
    if(!deletedActivity) return;
    deletedActivity.parent.appendChild(deletedActivity.row);
    deletedActivity = null;
    if(typeof showToast === 'function') showToast('Deletion cancelled', 'success', 1500);
}

// Make undoDelete globally accessible
window.undoDelete = undoDelete;

// ================== Quick Actions - Template-based quick add ==================

window.quickAddTemplate = function(template) {
    const templates = {
        'Meeting Follow-up': { desc: 'Follow-up from meeting - ', priority: 'High', source: 'Meeting' },
        'Awaiting Response': { desc: 'Awaiting response on: ', priority: 'Medium', source: 'Email' },
        'Research Task': { desc: 'Research: ', priority: 'Medium', source: 'Self' },
        'Review Needed': { desc: 'Review required for: ', priority: 'High', source: 'Review' }
    };
    
    const data = templates[template];
    if (!data) return;
    
    const desc = prompt(`${template}\n\nEnter activity description:`, data.desc);
    if (!desc || !desc.trim()) return;
    
    // Get the add_activity URL from the hidden data attribute
    const addActivityUrl = document.getElementById('add-activity-url')?.value || '/activities/add';
    
    // Create form and submit
    const form = document.createElement('form');
    form.method = 'POST';
    form.action = addActivityUrl;
    
    const fields = {
        'activity_desc': desc,
        'priority': data.priority,
        'source': data.source,
        'start_date': new Date().toISOString().split('T')[0],
        'status': 'Ongoing'
    };
    
    for (const [key, value] of Object.entries(fields)) {
        const input = document.createElement('input');
        input.type = 'hidden';
        input.name = key;
        input.value = value;
        form.appendChild(input);
    }
    
    document.body.appendChild(form);
    form.submit();
};

// ================== Bulk Actions ==================

let bulkMode = false;
let selectedActivities = new Set();

window.toggleBulkMode = function() {
    bulkMode = !bulkMode;
    selectedActivities.clear();
    
    const checkboxes = document.querySelectorAll('.bulk-checkbox');
    const bulkBtns = document.querySelectorAll('#bulkCloseBtn, #bulkPriorityBtn, #cancelBulkBtn');
    const bulkModeBtn = document.getElementById('bulkModeBtn');
    
    if (bulkMode) {
        checkboxes.forEach(cb => cb.classList.remove('hidden'));
        bulkBtns.forEach(btn => btn.classList.remove('hidden'));
        bulkModeBtn.classList.add('hidden');
    } else {
        checkboxes.forEach(cb => {
            cb.classList.add('hidden');
            cb.checked = false;
        });
        bulkBtns.forEach(btn => btn.classList.add('hidden'));
        bulkModeBtn.classList.remove('hidden');
    }
};

window.cancelBulkMode = function() {
    bulkMode = false;
    toggleBulkMode();
};

window.bulkCloseSelected = function() {
    const checkboxes = document.querySelectorAll('.bulk-checkbox:checked');
    if (checkboxes.length === 0) {
        if (typeof showToast === 'function') showToast('No activities selected', 'error');
        return;
    }
    
    if (!confirm(`Close ${checkboxes.length} selected activities?`)) return;
    
    let completed = 0;
    const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content;
    const headers = { 'Content-Type': 'application/json' };
    if (csrfToken) {
        headers['X-CSRFToken'] = csrfToken;
        headers['X-CSRF-Token'] = csrfToken;
    }
    
    checkboxes.forEach(cb => {
        const id = cb.getAttribute('data-activity-id');
        fetch('/activity/' + id + '/status', {
            method: 'POST',
            headers: headers,
            body: JSON.stringify({ status: 'Closed' })
        }).then(() => {
            completed++;
            if (completed === checkboxes.length) {
                if (typeof showToast === 'function') showToast(`Closed ${completed} activities`, 'success');
                setTimeout(() => window.location.reload(), 1000);
            }
        });
    });
};

window.bulkSetPriority = function() {
    const checkboxes = document.querySelectorAll('.bulk-checkbox:checked');
    if (checkboxes.length === 0) {
        if (typeof showToast === 'function') showToast('No activities selected', 'error');
        return;
    }
    
    const priority = prompt('Set priority for selected activities:\n\nEnter: High, Medium, or Low');
    if (!priority || !['High', 'Medium', 'Low'].includes(priority)) {
        if (typeof showToast === 'function') showToast('Invalid priority', 'error');
        return;
    }
    
    const activityIds = Array.from(checkboxes).map(cb => parseInt(cb.dataset.activityId));
    
    fetch('/activities/bulk/priority', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ activity_ids: activityIds, priority: priority })
    })
    .then(res => res.json())
    .then(data => {
        if (data.ok) {
            if (typeof showToast === 'function') showToast(`Updated ${data.updated_count} activities to ${priority}`, 'success');
            setTimeout(() => window.location.reload(), 1000);
        } else {
            if (typeof showToast === 'function') showToast('Error: ' + data.error, 'error');
        }
    })
    .catch(err => {
        if (typeof showToast === 'function') showToast('Network error', 'error');
    });
};

// ================== Focus Mode ==================

let focusModeActive = localStorage.getItem('focusMode') === 'true';

window.toggleFocusMode = function() {
    focusModeActive = !focusModeActive;
    localStorage.setItem('focusMode', focusModeActive);
    
    const btn = document.getElementById('focusModeBtn');
    const text = document.getElementById('focusModeText');
    const hint = document.getElementById('focusModeHint');
    const searchFilter = document.querySelector('.glass.rounded-lg.shadow-xl.p-4.mb-6');
    const quickActions = searchFilter ? searchFilter.nextElementSibling : null;
    const smartSuggestions = quickActions ? quickActions.nextElementSibling : null;
    const goalsSection = document.querySelector('.glass.rounded-lg.shadow-xl.p-6.mb-8');
    const prioritySections = document.querySelectorAll('[data-priority-section]');
    
    if (focusModeActive) {
        // Hide everything except top 3 high-priority items
        if (searchFilter) searchFilter.classList.add('hidden');
        if (quickActions && quickActions.querySelector('.fas.fa-bolt')) quickActions.classList.add('hidden');
        if (smartSuggestions && smartSuggestions.querySelector('.fas.fa-lightbulb')) smartSuggestions.classList.add('hidden');
        if (goalsSection) goalsSection.classList.add('hidden');
        
        // Show only top 3 high-priority items
        prioritySections.forEach(section => {
            const priority = section.getAttribute('data-priority-section');
            if (priority === 'High') {
                section.classList.remove('hidden');
                const rows = section.querySelectorAll('tbody tr');
                rows.forEach((row, idx) => {
                    if (idx >= 3) row.classList.add('hidden');
                    else row.classList.remove('hidden');
                });
            } else {
                section.classList.add('hidden');
            }
        });
        
        text.textContent = 'Exit Focus Mode';
        btn.classList.add('bg-primary', 'text-white');
        hint.classList.remove('hidden');
        document.body.classList.add('focus-mode');
    } else {
        // Show everything
        if (searchFilter) searchFilter.classList.remove('hidden');
        if (quickActions && quickActions.querySelector('.fas.fa-bolt')) quickActions.classList.remove('hidden');
        if (smartSuggestions && smartSuggestions.querySelector('.fas.fa-lightbulb')) smartSuggestions.classList.remove('hidden');
        if (goalsSection) goalsSection.classList.remove('hidden');
        
        prioritySections.forEach(section => {
            section.classList.remove('hidden');
            const rows = section.querySelectorAll('tbody tr');
            rows.forEach(row => row.classList.remove('hidden'));
        });
        
        text.textContent = 'Enter Focus Mode';
        btn.classList.remove('bg-primary', 'text-white');
        hint.classList.add('hidden');
        document.body.classList.remove('focus-mode');
    }
};

// ================== Event Listeners ==================

// Close modals on escape key
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        closeUpdateModal();
        closeClosingNoteModal();
    }
});

// Event delegation for quick update buttons
document.addEventListener('click', function(e) {
    const btn = e.target.closest('.quick-update-btn');
    if (!btn) return;
    const id = btn.getAttribute('data-id');
    const desc = btn.getAttribute('data-desc') || '';
    const bp = btn.getAttribute('data-bp') || '';
    openUpdateModal(id, desc, bp);
});

// Event delegation for status edit/save/cancel
document.addEventListener('click', function(e) {
    const editBtn = e.target.closest('.edit-status-btn');
    if (editBtn) {
        debugLog('Edit button clicked, id:', editBtn.getAttribute('data-id'));
        const id = editBtn.getAttribute('data-id');
        const cur = editBtn.getAttribute('data-current') || 'Ongoing';
        startEditStatus(id, cur);
        return;
    }
    const saveBtn = e.target.closest('.save-status-btn');
    if (saveBtn) {
        debugLog('Save button clicked, id:', saveBtn.getAttribute('data-id'));
        const id = saveBtn.getAttribute('data-id');
        saveStatus(id);
        return;
    }
    const cancelBtn = e.target.closest('.cancel-status-btn');
    if (cancelBtn) {
        debugLog('Cancel button clicked, id:', cancelBtn.getAttribute('data-id'));
        const id = cancelBtn.getAttribute('data-id');
        cancelStatus(id);
        return;
    }
    const snapTgl = e.target.closest('.snapshot-toggle');
    if (snapTgl) {
        const wrap = snapTgl.closest('.bp-snapshot');
        if (!wrap) return;
        const full = wrap.getAttribute('data-full') || '';
        if (snapTgl.getAttribute('data-state') === 'collapsed') {
            wrap.innerHTML = `${full} <button type="button" class="text-[10px] underline snapshot-toggle" data-state="expanded">less</button>`;
        } else {
            const short = (full.length > 100) ? full.slice(0,100) + '...' : full;
            wrap.innerHTML = `${short} <button type="button" class="text-[10px] underline snapshot-toggle" data-state="collapsed">more</button>`;
        }
        return;
    }
});

// Row-level keyboard shortcuts
document.addEventListener('keydown', function(e){
    // Don't trigger when typing in inputs
    if(['INPUT','TEXTAREA','SELECT'].includes(e.target.tagName)) return;
    
    const row = e.target.closest('tr[data-activity-id]');
    
    // Row-specific shortcuts (require focus on row)
    if(row) {
        const id = row.getAttribute('data-activity-id');
        const desc = row.getAttribute('data-activity-desc') || '';
        const bp = row.getAttribute('data-activity-bp') || '';
        const status = row.getAttribute('data-activity-status') || 'Ongoing';
        
        if(e.key === 'u' || e.key === 'U'){
            e.preventDefault();
            openUpdateModal(id, desc, bp);
        }
        if(e.key === 's' || e.key === 'S'){
            e.preventDefault();
            startEditStatus(id, status);
        }
        if(e.key === 'e' || e.key === 'E'){
            e.preventDefault();
            window.location.href = '/edit/' + id;
        }
    }
    
    // Global navigation shortcuts (work anywhere)
    if(e.key === 'j' || e.key === 'J'){
        e.preventDefault();
        navigateRows('down');
    }
    if(e.key === 'k' || e.key === 'K'){
        e.preventDefault();
        navigateRows('up');
    }
    if(e.key === 'a' || e.key === 'A'){
        e.preventDefault();
        window.location.href = '/add';
    }
});

function navigateRows(direction) {
    const rows = Array.from(document.querySelectorAll('tr[data-activity-id]'));
    if(rows.length === 0) return;
    
    const activeRow = document.activeElement.closest('tr[data-activity-id]');
    
    if(!activeRow) {
        // No row focused, focus the first one
        rows[0].tabIndex = 0;
        rows[0].focus();
        return;
    }
    
    const currentIndex = rows.indexOf(activeRow);
    let nextIndex;
    
    if(direction === 'down') {
        nextIndex = currentIndex + 1;
        if(nextIndex >= rows.length) nextIndex = 0; // Wrap to top
    } else {
        nextIndex = currentIndex - 1;
        if(nextIndex < 0) nextIndex = rows.length - 1; // Wrap to bottom
    }
    
    rows[nextIndex].tabIndex = 0;
    rows[nextIndex].focus();
    rows[nextIndex].scrollIntoView({ behavior: 'smooth', block: 'center' });
}

// Ensure modal form submits with CSRF token reliably
document.addEventListener('submit', function(e){
    const form = e.target.id === 'quickUpdateForm' ? e.target : null;
    if(!form) return;
    e.preventDefault();
    const action = form.getAttribute('action');
    const fd = new FormData(form);
    
    debugLog('Submitting update to:', action);
    debugLog('Form data entries:', Array.from(fd.entries()));
    
    // Attach CSRF from meta as a fallback in case hidden input is missing/stale
    const metaToken = document.querySelector('meta[name="csrf-token"]')?.content;
    if(metaToken && !fd.get('csrf_token')){
        fd.append('csrf_token', metaToken);
    }
    const headers = {};
    const tokenForHeader = fd.get('csrf_token') || metaToken;
    if (tokenForHeader) {
        headers['X-CSRFToken'] = tokenForHeader;
        headers['X-CSRF-Token'] = tokenForHeader;
    }
    fetch(action, {
        method: 'POST',
        body: fd,
        headers: headers,
        credentials: 'same-origin'
    }).then(r=>{
        if(!r.ok) {
            return r.text().then(text => {
                debugLog('Server response:', text);
                throw new Error(`Server error: ${r.status}`);
            });
        }
        if(typeof showToast === 'function') showToast('Update added', 'success');
        // Clear inputs and close modal
        form.reset();
        closeUpdateModal();
        setTimeout(()=>window.location.reload(), 500);
    }).catch(err=>{
        debugLog('Error adding update:', err);
        if(typeof showToast === 'function') showToast('Error adding update: ' + err.message, 'error');
    });
});

// Delete with undo
document.addEventListener('click', function(e){
    const delBtn = e.target.closest('.delete-activity-btn');
    if(!delBtn) return;
    e.preventDefault();
    const id = delBtn.getAttribute('data-id');
    const desc = delBtn.getAttribute('data-desc') || 'this activity';
    const row = delBtn.closest('tr');
    if(!row) return;
    // Store for undo
    deletedActivity = { id: id, row: row.cloneNode(true), parent: row.parentNode };
    row.remove();
    // Show toast with undo
    if(typeof showToast === 'function'){
        const wrap = document.getElementById('toast-container'); if(!wrap) return;
        const d=document.createElement('div'); d.className='toast toast-info';
        d.innerHTML = `<span>Deleted "${desc}"</span><button class='ml-2 underline' onclick='undoDelete()'>Undo</button>`;
        wrap.appendChild(d);
        setTimeout(()=>{
            if(deletedActivity && deletedActivity.id === id){
                fetch('/delete/' + id).then(()=>{ deletedActivity = null; });
            }
            d.style.opacity='0'; d.style.transition='opacity .3s'; setTimeout(()=>d.remove(),300);
        }, 15000);
    } else {
        // Fallback: immediate delete
        fetch('/delete/' + id).then(()=>window.location.reload());
    }
});

// Inline quick update with Ctrl+Enter
document.addEventListener('keydown', function(e){
    if((e.ctrlKey || e.metaKey) && e.key === 'Enter'){
        const inp = e.target.closest('.inline-update-input');
        if(!inp) return;
        e.preventDefault();
        const id = inp.getAttribute('data-activity-id');
        const text = inp.value.trim();
        if(!text) return;
    // Submit update - need to include CSRF token
        const form = new FormData();
        form.append('update_text', text);
        form.append('redirect', 'dashboard');
        
        // Get CSRF token from meta tag or hidden input
        const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content || 
                         document.querySelector('input[name="csrf_token"]')?.value;
        if(csrfToken) {
            form.append('csrf_token', csrfToken);
        }
        
        const headers = {};
        if (csrfToken) {
            headers['X-CSRFToken'] = csrfToken;
            headers['X-CSRF-Token'] = csrfToken;
        }
        fetch('/activity/' + id + '/update', { 
            method: 'POST', 
            body: form,
            headers: headers,
            credentials: 'same-origin'
        })
            .then(r=>{
                if(!r.ok) {
                    return r.text().then(text => {
                        debugLog('Server response:', text);
                        throw new Error(`Server error: ${r.status}`);
                    });
                }
                return r;
            })
            .then(()=>{
                if(typeof showToast === 'function') showToast('Update added', 'success');
                inp.value = '';
                // Reload page to show new update
                setTimeout(()=>window.location.reload(), 800);
            })
            .catch(err=>{
                debugLog('Error adding update:', err);
                if(typeof showToast === 'function') showToast('Error adding update: ' + err.message, 'error');
            });
    }
});

// Apply focus mode on load if active
if (focusModeActive) {
    setTimeout(toggleFocusMode, 100);
}

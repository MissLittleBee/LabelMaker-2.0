// Global variables
let currentEditingForm = null;
let deleteFormName = null;

// Load forms on page load
document.addEventListener('DOMContentLoaded', function () {
    // Set the sort select to match URL parameter
    const urlParams = new URLSearchParams(window.location.search);
    const sortBy = urlParams.get('sort') || 'name';
    const sortSelect = document.getElementById('sortSelect');
    if (sortSelect) {
        sortSelect.value = sortBy;
    }

    loadForms();
});

// Load all forms from API
async function loadForms() {
    try {
        // Get sort parameter from current URL
        const urlParams = new URLSearchParams(window.location.search);
        const sortBy = urlParams.get('sort') || 'name';
        console.log('Loading forms with sort:', sortBy);

        const response = await fetch(`/api/form?sort=${sortBy}`);
        const data = await response.json();

        const tbody = document.getElementById('formsTableBody');
        const emptyState = document.getElementById('emptyState');

        if (!data.forms || data.forms.length === 0) {
            tbody.innerHTML = '';
            emptyState.style.display = 'block';
            return;
        }

        emptyState.style.display = 'none';
        tbody.innerHTML = '';

        data.forms.forEach(form => {
            const row = createFormRow(form);
            tbody.appendChild(row);
        });

    } catch (error) {
        console.error('Error loading forms:', error);
        const tbody = document.getElementById('formsTableBody');
        tbody.innerHTML = `
            <tr>
                <td colspan="4" style="text-align: center; color: #dc3545;">
                    ❌ Chyba při načítání dat: ${error.message}
                </td>
            </tr>
        `;
    }
}

// Create table row for a form
function createFormRow(form) {
    const tr = document.createElement('tr');

    // Format unit display
    const unitDisplay = {
        'weight': 'Hmotnost',
        'volume': 'Objem',
        'piece': 'Kus',
        'length': 'Délka',
        'other': 'Jiné'
    };

    tr.innerHTML = `
        <td><strong>${escapeHtml(form.name)}</strong></td>
        <td><code>${escapeHtml(form.short_name)}</code></td>
        <td>${unitDisplay[form.unit] || form.unit}</td>
        <td>
            <div class="table-actions">
                <button class="btn btn-small btn-primary" onclick="openEditModal('${escapeHtml(form.name)}')">
                    ✏️ Upravit
                </button>
                <button class="btn btn-small btn-danger" onclick="openDeleteModal('${escapeHtml(form.name)}')">
                    🗑️ Smazat
                </button>
            </div>
        </td>
    `;

    return tr;
}

// Open create modal
function openCreateModal() {
    currentEditingForm = null;
    document.getElementById('modalTitle').textContent = 'Vytvořit novou formu';
    document.getElementById('submitBtn').textContent = 'Vytvořit';
    document.getElementById('formForm').reset();
    document.getElementById('formModal').classList.add('active');
}

// Open edit modal
async function openEditModal(formName) {
    try {
        const response = await fetch('/api/form');
        const data = await response.json();
        const form = data.forms.find(f => f.name === formName);

        if (!form) {
            alert('Forma nenalezena');
            return;
        }

        currentEditingForm = formName;
        document.getElementById('modalTitle').textContent = 'Upravit formu';
        document.getElementById('submitBtn').textContent = 'Uložit změny';

        document.getElementById('formName').value = form.name;
        document.getElementById('formShortName').value = form.short_name;
        document.getElementById('formUnit').value = form.unit;

        document.getElementById('formModal').classList.add('active');

    } catch (error) {
        console.error('Error loading form:', error);
        alert('Chyba při načítání dat formy');
    }
}

// Close form modal
function closeModal() {
    document.getElementById('formModal').classList.remove('active');
    document.getElementById('formForm').reset();
    currentEditingForm = null;
}

// Handle form submission
async function handleSubmit(event) {
    event.preventDefault();

    const formData = {
        name: document.getElementById('formName').value.trim(),
        short_name: document.getElementById('formShortName').value.trim(),
        unit: document.getElementById('formUnit').value
    };

    try {
        const method = currentEditingForm ? 'PUT' : 'POST';
        const url = '/api/form';

        const response = await fetch(url, {
            method: method,
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });

        const data = await response.json();

        if (response.ok) {
            closeModal();
            loadForms();
            showNotification(currentEditingForm ? 'Forma byla aktualizována' : 'Forma byla vytvořena', 'success');
        } else {
            alert('Chyba: ' + (data.error || 'Neznámá chyba'));
        }

    } catch (error) {
        console.error('Error submitting form:', error);
        alert('Chyba při odesílání dat: ' + error.message);
    }
}

// Open delete confirmation modal
function openDeleteModal(formName) {
    deleteFormName = formName;
    document.getElementById('deleteFormName').textContent = formName;
    document.getElementById('deleteModal').classList.add('active');
}

// Close delete modal
function closeDeleteModal() {
    document.getElementById('deleteModal').classList.remove('active');
    deleteFormName = null;
}

// Confirm and execute delete
async function confirmDelete() {
    if (!deleteFormName) return;

    try {
        const response = await fetch('/api/form', {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ name: deleteFormName })
        });

        const data = await response.json();

        if (response.ok) {
            closeDeleteModal();
            loadForms();
            showNotification('Forma byla smazána', 'success');
        } else {
            alert('Chyba: ' + (data.error || 'Neznámá chyba'));
        }

    } catch (error) {
        console.error('Error deleting form:', error);
        alert('Chyba při mazání: ' + error.message);
    }
}

// Show notification with toast
function showNotification(message, type) {
    // Create toast container if it doesn't exist
    let toastContainer = document.getElementById('toastContainer');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.id = 'toastContainer';
        toastContainer.className = 'toast-container';
        document.body.appendChild(toastContainer);
    }

    // Create toast element
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;

    const icon = type === 'success' ? '✓' : type === 'error' ? '✗' : 'ℹ';
    toast.innerHTML = `
        <span class="toast-icon">${icon}</span>
        <span class="toast-message">${message}</span>
    `;

    toastContainer.appendChild(toast);

    // Trigger animation
    setTimeout(() => toast.classList.add('show'), 10);

    // Remove after 3 seconds
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// Escape HTML to prevent XSS
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Close modal when clicking outside
window.onclick = function (event) {
    const formModal = document.getElementById('formModal');
    const deleteModal = document.getElementById('deleteModal');

    if (event.target === formModal) {
        closeModal();
    }
    if (event.target === deleteModal) {
        closeDeleteModal();
    }
}

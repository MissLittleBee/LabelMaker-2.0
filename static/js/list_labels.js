// Global variables
let allLabels = [];
let currentEditingId = null;
let deleteLabelId = null;

// Load labels on page load
document.addEventListener('DOMContentLoaded', function () {
    loadLabels();

    // Add event listeners for filters
    document.getElementById('searchInput').addEventListener('input', filterLabels);
    document.getElementById('printFilter').addEventListener('change', filterLabels);
});

// Load all labels from API
async function loadLabels() {
    try {
        const response = await fetch('/api/labels');
        const data = await response.json();

        allLabels = data.labels || [];
        displayLabels(allLabels);

    } catch (error) {
        console.error('Error loading labels:', error);
        showNotification('Chyba při načítání cenovek: ' + error.message, 'error');
    }
}

// Display labels in table
function displayLabels(labels) {
    const tbody = document.getElementById('labelsTableBody');
    const emptyState = document.getElementById('emptyState');

    if (!labels || labels.length === 0) {
        tbody.innerHTML = '';
        emptyState.style.display = 'block';
        return;
    }

    emptyState.style.display = 'none';
    tbody.innerHTML = '';

    labels.forEach(label => {
        const row = createLabelRow(label);
        tbody.appendChild(row);
    });
}

// Create table row for a label
function createLabelRow(label) {
    const tr = document.createElement('tr');
    tr.dataset.labelId = label.id;

    const printBadge = label.marked_to_print
        ? '<span class="print-badge marked">✓ Ano</span>'
        : '<span class="print-badge unmarked">✗ Ne</span>';

    tr.innerHTML = `
        <td><strong>${escapeHtml(label.product_name)}</strong></td>
        <td>${escapeHtml(label.form)}</td>
        <td>${label.amount}</td>
        <td>${label.price} Kč</td>
        <td>${label.unit_price} Kč</td>
        <td class="print-toggle-container">
            <label class="print-toggle">
                <input type="checkbox" ${label.marked_to_print ? 'checked' : ''} onchange="togglePrintMark(${label.id})">
                <span class="print-toggle-slider"></span>
            </label>
        </td>
        <td>
            <div class="table-actions">
                <button class="btn btn-small btn-primary" onclick="openEditModal(${label.id})">
                    ✏️ Upravit
                </button>
                <button class="btn btn-small btn-danger" onclick="openDeleteModal(${label.id}, '${escapeHtml(label.product_name)}')">
                    🗑️ Smazat
                </button>
            </div>
        </td>
    `;

    return tr;
}

// Filter labels based on search and print status
function filterLabels() {
    const searchTerm = document.getElementById('searchInput').value.toLowerCase();
    const printFilter = document.getElementById('printFilter').value;

    let filtered = allLabels.filter(label => {
        // Text search
        const matchesSearch = label.product_name.toLowerCase().includes(searchTerm);

        // Print filter
        let matchesPrint = true;
        if (printFilter === 'marked') {
            matchesPrint = label.marked_to_print === true;
        } else if (printFilter === 'unmarked') {
            matchesPrint = label.marked_to_print === false;
        }

        return matchesSearch && matchesPrint;
    });

    displayLabels(filtered);
}

// Toggle print mark for a label
async function togglePrintMark(labelId) {
    try {
        const response = await fetch(`/api/label/${labelId}/toggle-print`, {
            method: 'POST'
        });

        const data = await response.json();

        if (response.ok) {
            // Update local data
            const label = allLabels.find(l => l.id === labelId);
            if (label) {
                label.marked_to_print = data.marked_to_print;
            }
            filterLabels();
            showNotification('Označení k tisku změněno', 'success');
        } else {
            showNotification('Chyba: ' + (data.error || 'Neznámá chyba'), 'error');
        }
    } catch (error) {
        console.error('Error toggling print mark:', error);
        showNotification('Chyba při změně označení', 'error');
    }
}

// Open edit modal
function openEditModal(labelId) {
    const label = allLabels.find(l => l.id === labelId);
    if (!label) {
        showNotification('Cenovka nenalezen', 'error');
        return;
    }

    currentEditingId = labelId;
    document.getElementById('editLabelId').value = labelId;
    document.getElementById('editProductName').value = label.product_name;
    document.getElementById('editForm').value = label.form;
    document.getElementById('editAmount').value = label.amount;
    document.getElementById('editPrice').value = label.price;

    document.getElementById('editModal').classList.add('active');
}

// Close edit modal
function closeEditModal() {
    document.getElementById('editModal').classList.remove('active');
    document.getElementById('editForm').reset();
    currentEditingId = null;
}

// Handle edit form submission
async function handleEditSubmit(event) {
    event.preventDefault();

    const labelId = currentEditingId;
    const formData = {
        product_name: document.getElementById('editProductName').value.trim(),
        form: document.getElementById('editForm').value,
        amount: parseFloat(document.getElementById('editAmount').value),
        price: parseFloat(document.getElementById('editPrice').value)
    };

    try {
        const response = await fetch(`/api/label/${labelId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });

        const data = await response.json();

        if (response.ok) {
            closeEditModal();
            loadLabels();
            showNotification('Cenovka byl aktualizován', 'success');
        } else {
            showNotification('Chyba: ' + (data.error || 'Neznámá chyba'), 'error');
        }
    } catch (error) {
        console.error('Error updating label:', error);
        showNotification('Chyba při aktualizaci cenovky', 'error');
    }
}

// Open delete confirmation modal
function openDeleteModal(labelId, productName) {
    deleteLabelId = labelId;
    document.getElementById('deleteLabelName').textContent = productName;
    document.getElementById('deleteModal').classList.add('active');
}

// Close delete modal
function closeDeleteModal() {
    document.getElementById('deleteModal').classList.remove('active');
    deleteLabelId = null;
}

// Confirm and execute delete
async function confirmDelete() {
    if (!deleteLabelId) return;

    try {
        const response = await fetch(`/api/label/${deleteLabelId}`, {
            method: 'DELETE'
        });

        const data = await response.json();

        if (response.ok) {
            closeDeleteModal();
            loadLabels();
            showNotification('Cenovka byl smazán', 'success');
        } else {
            showNotification('Chyba: ' + (data.error || 'Neznámá chyba'), 'error');
        }
    } catch (error) {
        console.error('Error deleting label:', error);
        showNotification('Chyba při mazání cenovky', 'error');
    }
}

// Show notification with toast
function showNotification(message, type) {
    let toastContainer = document.getElementById('toastContainer');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.id = 'toastContainer';
        toastContainer.className = 'toast-container';
        document.body.appendChild(toastContainer);
    }

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;

    const icon = type === 'success' ? '✓' : type === 'error' ? '✗' : 'ℹ';
    toast.innerHTML = `
        <span class="toast-icon">${icon}</span>
        <span class="toast-message">${message}</span>
    `;

    toastContainer.appendChild(toast);
    setTimeout(() => toast.classList.add('show'), 10);

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
    const editModal = document.getElementById('editModal');
    const deleteModal = document.getElementById('deleteModal');

    if (event.target === editModal) {
        closeEditModal();
    }
    if (event.target === deleteModal) {
        closeDeleteModal();
    }
}

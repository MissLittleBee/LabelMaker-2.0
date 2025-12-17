// Calculate and display unit price when amount or price changes
function updateUnitPrice() {
    const amount = parseFloat(document.getElementById('amount').value);
    const price = parseFloat(document.getElementById('price').value);
    const display = document.getElementById('unitPriceDisplay');

    if (amount > 0 && price >= 0) {
        const unitPrice = (price / amount).toFixed(2);
        display.textContent = `${unitPrice} Kč`;
    } else {
        display.textContent = '-- Kč';
    }
}

// Add event listeners
document.getElementById('amount').addEventListener('input', updateUnitPrice);
document.getElementById('price').addEventListener('input', updateUnitPrice);

// Handle form submission
async function handleSubmit(event) {
    event.preventDefault();

    const formData = {
        product_name: document.getElementById('productName').value.trim(),
        form: document.getElementById('form').value,
        amount: parseFloat(document.getElementById('amount').value),
        price: parseFloat(document.getElementById('price').value),
        marked_to_print: document.getElementById('markedToPrint').checked
    };

    try {
        const response = await fetch('/api/label', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });

        const data = await response.json();

        if (response.ok) {
            showNotification('Štítek byl úspěšně vytvořen!', 'success');
            setTimeout(() => {
                window.location.href = '/labels/new';
            }, 1500);
        } else {
            showNotification('Chyba: ' + (data.error || 'Neznámá chyba'), 'error');
        }

    } catch (error) {
        console.error('Error submitting form:', error);
        showNotification('Chyba při odesílání dat: ' + error.message, 'error');
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

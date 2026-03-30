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
        const response = await fetch('/labels/api/label', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });

        const data = await response.json();

        if (response.ok) {
            showNotification('Cenovka byl úspěšně vytvořen!', 'success');
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

// Show notification with toast — provided by shared.js (showNotification)

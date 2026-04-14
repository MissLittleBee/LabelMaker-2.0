/**
 * Shared utility functions for LabelMaker.
 * Provides toast notifications, HTML escaping, and modal helpers.
 */

/**
 * Show a toast notification.
 * @param {string} message - The message to display.
 * @param {'success'|'error'|'info'} type - The notification type.
 */
function showNotification(message, type = 'success') {
    let toastContainer = document.getElementById('toastContainer');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.id = 'toastContainer';
        toastContainer.className = 'toast-container';
        document.body.appendChild(toastContainer);
    }

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;

    const icons = { success: '✓', error: '✗', info: 'ℹ' };

    const iconSpan = document.createElement('span');
    iconSpan.className = 'toast-icon';
    iconSpan.textContent = icons[type] || icons.info;

    const messageSpan = document.createElement('span');
    messageSpan.className = 'toast-message';
    messageSpan.textContent = message;

    toast.appendChild(iconSpan);
    toast.appendChild(messageSpan);
    toastContainer.appendChild(toast);

    setTimeout(() => toast.classList.add('show'), 10);
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

/**
 * Escape HTML to prevent XSS attacks.
 * @param {string} text - The text to escape.
 * @returns {string} The escaped HTML string.
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Format a number for Czech display (comma decimal separator, strip trailing zeros).
 * @param {number} value - The number to format.
 * @param {number} [decimals=2] - Maximum decimal places.
 * @returns {string} Formatted number string.
 */
function formatCzechNumber(value, decimals = 2) {
    if (Number.isInteger(value) || value === Math.floor(value)) {
        return String(Math.floor(value));
    }
    return value.toFixed(decimals).replace(/0+$/, '').replace(/\.$/, '').replace('.', ',');
}

/**
 * Format a price for Czech labels: '352,-' for whole, '29,90' for decimals.
 * @param {number} value - The price value.
 * @returns {string} Formatted price string.
 */
function formatCzechPrice(value) {
    if (Number.isInteger(value) || value === Math.floor(value)) {
        return Math.floor(value) + ',-';
    }
    return value.toFixed(2).replace('.', ',');
}

/**
 * Keep desktop launcher alive only while browser window remains open.
 */
(function initAppHeartbeat() {
    if (typeof window === 'undefined' || typeof navigator === 'undefined') {
        return;
    }

    const sendHeartbeat = () => {
        const payload = JSON.stringify({ ts: Date.now() });

        if (navigator.sendBeacon) {
            const blob = new Blob([payload], { type: 'application/json' });
            navigator.sendBeacon('/heartbeat', blob);
            return;
        }

        fetch('/heartbeat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: payload,
            keepalive: true,
        }).catch(() => {
            // Heartbeat failures are non-fatal and retried on next interval.
        });
    };

    sendHeartbeat();
    const intervalId = window.setInterval(sendHeartbeat, 5000);

    window.addEventListener('beforeunload', () => {
        sendHeartbeat();
        window.clearInterval(intervalId);
    });
})();

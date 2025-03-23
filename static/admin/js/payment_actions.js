function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function approvePayment(paymentId) {
    if (confirm('To\'lovni tasdiqlashni xohlaysizmi?')) {
        updatePaymentStatus(paymentId, 'COMPLETED');
    }
}

function rejectPayment(paymentId) {
    if (confirm('To\'lovni rad etishni xohlaysizmi?')) {
        updatePaymentStatus(paymentId, 'REJECTED');
    }
}

function updatePaymentStatus(paymentId, status) {
    const csrftoken = getCookie('csrftoken');
    
    fetch(`/api/payments/${paymentId}/update-status/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrftoken,
        },
        body: JSON.stringify({ status: status })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            location.reload();
        } else {
            alert('Xatolik yuz berdi: ' + data.message);
        }
    })
    .catch(error => {
        alert('Xatolik yuz berdi: ' + error);
    });
} 
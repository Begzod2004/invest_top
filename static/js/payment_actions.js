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

async function approvePayment(paymentId) {
    try {
        if (!confirm('To\'lovni tasdiqlashni xohlaysizmi?')) {
            return;
        }

        const response = await fetch(`/admin/payments/payment/approve/${paymentId}/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken'),
                'Accept': 'application/json'
            }
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.message || 'Xatolik yuz berdi');
        }

        // Muvaffaqiyatli natija
        Swal.fire({
            title: 'Muvaffaqiyatli!',
            text: data.message,
            icon: 'success',
            confirmButtonText: 'OK'
        }).then(() => {
            location.reload();
        });

    } catch (error) {
        console.error('Xatolik:', error);
        Swal.fire({
            title: 'Xatolik!',
            text: error.message || 'Tizimda xatolik yuz berdi',
            icon: 'error',
            confirmButtonText: 'OK'
        });
    }
}

async function rejectPayment(paymentId) {
    try {
        const result = await Swal.fire({
            title: 'To\'lovni rad etish',
            text: 'Rad etish sababini kiriting:',
            input: 'text',
            inputPlaceholder: 'Sabab...',
            showCancelButton: true,
            confirmButtonText: 'Rad etish',
            cancelButtonText: 'Bekor qilish',
            inputValidator: (value) => {
                if (!value) {
                    return 'Rad etish sababini kiritish majburiy!';
                }
            }
        });

        if (!result.isConfirmed) {
            return;
        }

        const response = await fetch(`/admin/payments/payment/reject/${paymentId}/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken'),
                'Accept': 'application/json'
            },
            body: JSON.stringify({
                reason: result.value
            })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.message || 'Xatolik yuz berdi');
        }

        // Muvaffaqiyatli natija
        Swal.fire({
            title: 'Muvaffaqiyatli!',
            text: data.message,
            icon: 'success',
            confirmButtonText: 'OK'
        }).then(() => {
            location.reload();
        });

    } catch (error) {
        console.error('Xatolik:', error);
        Swal.fire({
            title: 'Xatolik!',
            text: error.message || 'Tizimda xatolik yuz berdi',
            icon: 'error',
            confirmButtonText: 'OK'
        });
    }
}

async function updatePaymentStatus(paymentId, newStatus) {
    try {
        const response = await fetch(`/api/payments/${paymentId}/`, {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken'),
                'Accept': 'application/json'
            },
            body: JSON.stringify({
                status: newStatus
            })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.message || 'Xatolik yuz berdi');
        }

        return data;

    } catch (error) {
        console.error('Xatolik:', error);
        throw error;
    }
}

async function viewPaymentDetails(paymentId) {
    try {
        const response = await fetch(`/api/payments/${paymentId}/`);
        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.message || 'Xatolik yuz berdi');
        }

        Swal.fire({
            title: 'To\'lov ma\'lumotlari',
            html: `
                <div class="payment-details">
                    <p><strong>ID:</strong> ${data.id}</p>
                    <p><strong>Foydalanuvchi:</strong> ${data.user}</p>
                    <p><strong>Summa:</strong> ${data.amount}</p>
                    <p><strong>Holat:</strong> ${data.status}</p>
                    <p><strong>Sana:</strong> ${new Date(data.created_at).toLocaleString()}</p>
                    ${data.screenshot ? `<img src="${data.screenshot}" alt="To'lov skrini" style="max-width: 100%;">` : ''}
                </div>
            `,
            width: '600px'
        });

    } catch (error) {
        console.error('Xatolik:', error);
        Swal.fire({
            title: 'Xatolik!',
            text: error.message || 'Ma\'lumotlarni yuklashda xatolik yuz berdi',
            icon: 'error',
            confirmButtonText: 'OK'
        });
    }
}

document.addEventListener('DOMContentLoaded', function() {
    // To'lov jadvalini yangilash
    const refreshPaymentTable = () => {
        if (document.querySelector('.payment-list-table')) {
            location.reload();
        }
    };

    // Har 30 sekundda avtomatik yangilash
    setInterval(refreshPaymentTable, 30000);
}); 
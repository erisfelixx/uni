import { useState, useEffect } from 'react';
import api from '../api/axiosConfig';

// відповідність статусів бронювання до україномовних підписів
const statusLabels = {
    PENDING: 'Очікує підтвердження',
    CONFIRMED: 'Підтверджено',
    CANCELLED: 'Скасовано',
};

const statusColors = {
    PENDING: { color: '#7A5C00', backgroundColor: '#FFF8E1' },
    CONFIRMED: { color: '#1D6A3E', backgroundColor: '#E9F7EF' },
    CANCELLED: { color: '#A32D2D', backgroundColor: '#FAECE7' },
};

const styles = {
    page: {
        maxWidth: '720px',
        margin: '0 auto',
        padding: '2.5rem 1.25rem',
        fontFamily: "'Inter', sans-serif",
    },
    pageHeader: {
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'baseline',
        marginBottom: '2rem',
        paddingBottom: '1rem',
        borderBottom: '0.5px solid rgba(0,0,0,0.12)',
    },
    pageTitle: {
        fontSize: '22px',
        fontWeight: 500,
        margin: 0,
        letterSpacing: '-0.01em',
    },
    pageCount: {
        fontSize: '14px',
        color: '#888',
    },
    errorText: {
        fontSize: '13px',
        color: '#A32D2D',
        backgroundColor: '#FAECE7',
        padding: '10px 14px',
        borderRadius: '6px',
        marginBottom: '1.25rem',
    },
    emptyText: {
        fontSize: '14px',
        color: '#888',
        marginTop: '1rem',
    },
    grid: {
        display: 'flex',
        flexDirection: 'column',
        gap: '1rem',
    },
    card: {
        border: '0.5px solid rgba(0,0,0,0.12)',
        borderRadius: '12px',
        padding: '1.5rem',
        backgroundColor: '#fff',
        display: 'flex',
        flexDirection: 'column',
        gap: '1rem',
    },
    cardHeader: {
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
    },
    bookingId: {
        fontSize: '15px',
        fontWeight: 500,
        margin: 0,
        color: '#1a1a1a',
    },
    statusBadge: {
        fontSize: '11px',
        fontWeight: 500,
        textTransform: 'uppercase',
        letterSpacing: '0.05em',
        padding: '3px 10px',
        borderRadius: '6px',
    },
    cardBody: {
        display: 'grid',
        gridTemplateColumns: '1fr 1fr',
        gap: '0.5rem 1.5rem',
    },
    metaRow: {
        display: 'flex',
        flexDirection: 'column',
        gap: '2px',
    },
    metaLabel: {
        fontSize: '11px',
        color: '#aaa',
        textTransform: 'uppercase',
        letterSpacing: '0.05em',
    },
    metaValue: {
        fontSize: '14px',
        color: '#1a1a1a',
    },
    price: {
        fontSize: '20px',
        fontWeight: 500,
    },
    priceSub: {
        fontSize: '13px',
        fontWeight: 400,
        color: '#888',
        marginLeft: '2px',
    },
};

export default function MyBookingsPage() {
    const [bookings, setBookings] = useState([]);
    const [error, setError] = useState('');

    useEffect(() => {
        const fetchMyBookings = async () => {
            try {
                const token = localStorage.getItem('token');
                if (!token) return;

                // розшифровуємо токен, щоб дістати ID клієнта
                const payload = JSON.parse(atob(token.split('.')[1]));
                const customerId = payload.id;

                // робимо GET-запит за бронюваннями (якщо бекенд вимагає ID в параметрах)
                const response = await api.get(`/bookings?customerId=${customerId}`);
                setBookings(response.data);
            } catch (err) {
                setError('помилка завантаження бронювань: ' + (err.response?.data?.error || err.message));
            }
        };

        fetchMyBookings();
    }, []);

    return (
        <div style={styles.page}>
            <div style={styles.pageHeader}>
                <h2 style={styles.pageTitle}>Мої бронювання</h2>
                {bookings.length > 0 && (
                    <span style={styles.pageCount}>{bookings.length} {bookings.length === 1 ? 'бронювання' : 'бронювань'}</span>
                )}
            </div>

            {error && <p style={styles.errorText}>{error}</p>}

            {bookings.length === 0 ? (
                <p style={styles.emptyText}>У вас ще немає бронювань.</p>
            ) : (
                <div style={styles.grid}>
                    {bookings.map((booking) => {
                        const statusStyle = statusColors[booking.status] || { color: '#555', backgroundColor: '#f0f0f0' };
                        return (
                            <div key={booking.id} style={styles.card}>
                                <div style={styles.cardHeader}>
                                    <p style={styles.bookingId}>Бронювання #{booking.id}</p>
                                    <span style={{ ...styles.statusBadge, ...statusStyle }}>
                                        {statusLabels[booking.status] || booking.status}
                                    </span>
                                </div>

                                <div style={styles.cardBody}>
                                    <div style={styles.metaRow}>
                                        <span style={styles.metaLabel}>ID туру</span>
                                        <span style={styles.metaValue}>{booking.tourId}</span>
                                    </div>

                                    <div style={styles.metaRow}>
                                        <span style={styles.metaLabel}>Дата створення</span>
                                        <span style={styles.metaValue}>
                                            {new Date(booking.createdAt).toLocaleString('uk-UA', {
                                                day: '2-digit', month: '2-digit', year: 'numeric',
                                                hour: '2-digit', minute: '2-digit'
                                            })}
                                        </span>
                                    </div>

                                    <div style={styles.metaRow}>
                                        <span style={styles.metaLabel}>До сплати</span>
                                        <span style={{ ...styles.metaValue, ...styles.price }}>
                                            {Number(booking.finalPrice).toLocaleString('uk-UA')}
                                            <span style={styles.priceSub}> ₴</span>
                                        </span>
                                    </div>
                                </div>
                            </div>
                        );
                    })}
                </div>
            )}
        </div>
    );
}
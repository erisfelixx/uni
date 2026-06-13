import { useState, useEffect } from 'react';
import api from '../api/axiosConfig';

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
        color: '#A32D2D',
        fontSize: '14px',
        marginBottom: '1rem',
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
        display: 'flex',
        flexDirection: 'column',
        gap: '1rem',
        backgroundColor: '#fff',
    },
    cardTop: {
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'flex-start',
        gap: '1rem',
    },
    cardTitle: {
        fontSize: '18px',
        fontWeight: 500,
        margin: 0,
        lineHeight: 1.3,
    },
    hotBadge: {
        fontSize: '11px',
        fontWeight: 500,
        textTransform: 'uppercase',
        letterSpacing: '0.05em',
        color: '#993C1D',
        backgroundColor: '#FAECE7',
        padding: '3px 10px',
        borderRadius: '6px',
        whiteSpace: 'nowrap',
        flexShrink: 0,
        alignSelf: 'flex-start',
    },
    cardDesc: {
        fontSize: '14px',
        color: '#666',
        lineHeight: 1.65,
        margin: 0,
    },
    typePill: {
        display: 'inline-block',
        fontSize: '12px',
        color: '#666',
        backgroundColor: '#f5f5f5',
        padding: '3px 10px',
        borderRadius: '20px',
        border: '0.5px solid rgba(0,0,0,0.1)',
    },
    cardFooter: {
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        paddingTop: '1rem',
        borderTop: '0.5px solid rgba(0,0,0,0.1)',
    },
    price: {
        fontSize: '20px',
        fontWeight: 500,
        margin: 0,
    },
    priceSub: {
        fontSize: '13px',
        fontWeight: 400,
        color: '#888',
        marginLeft: '2px',
    },
    bookBtn: {
        padding: '8px 20px',
        backgroundColor: '#1a1a1a',
        color: '#fff',
        border: 'none',
        borderRadius: '8px',
        fontSize: '14px',
        fontWeight: 500,
        cursor: 'pointer',
        fontFamily: "'Inter', sans-serif",
        transition: 'opacity 0.15s',
    },
};

// локалізація назв типів туру для відображення користувачу
const tourTypeLabels = {
    REST: 'Відпочинок',
    EXCURSION: 'Екскурсія',
    SHOPPING: 'Шопінг',
};

export default function ToursPage() {
    const [tours, setTours] = useState([]);
    const [error, setError] = useState('');

    // функція, яка запускається один раз при відкритті сторінки
    useEffect(() => {
        const fetchTours = async () => {
            try {
                // робимо запит до нашого java api
                const response = await api.get('/tours');
                setTours(response.data);
            } catch (err) {
                setError('помилка завантаження турів: ' + err.message);
            }
        };

        fetchTours();
    }, []);

    // функція для створення бронювання при кліку на кнопку
    const handleBooking = async (tourId, basePrice) => {
        try {
            // дістаємо токен, щоб зрозуміти, хто зараз залогінений
            const token = localStorage.getItem('token');
            if (!token) {
                alert('будь ласка, увійдіть у систему!');
                return;
            }

            // розшифровуємо payload токена (це середня частина jwt), щоб дістати id користувача
            const payload = JSON.parse(atob(token.split('.')[1]));
            const customerId = payload.id;

            // формуємо дані для відправки на бекенд
            const bookingData = {
                customerId: customerId,
                tourId: tourId,
                finalPrice: basePrice
            };

            // відправляємо post-запит до booking servlet
            const response = await api.post('/bookings', bookingData);
            const savedBooking = response.data;

            // перевіряємо, чи бекенд застосував знижку, і показуємо відповідне повідомлення
            if (savedBooking.finalPrice < basePrice) {
                alert(`вітаю! тур успішно заброньовано.\n\nвам автоматично застосовано знижку лояльності 10%!\nпочаткова ціна: ${basePrice} ₴\nваша ціна: ${savedBooking.finalPrice} ₴`);
            } else {
                alert(`тур успішно заброньовано!\n\nдо сплати: ${savedBooking.finalPrice} ₴`);
            }

        } catch (err) {
            alert('помилка бронювання: ' + (err.response?.data?.error || err.message));
        }
    };

    return (
        <div style={styles.page}>
            <div style={styles.pageHeader}>
                <h2 style={styles.pageTitle}>Доступні тури</h2>
                <span style={styles.pageCount}>{tours.length} {tours.length === 1 ? 'тур' : 'тури'}</span>
            </div>

            {error && <p style={styles.errorText}>{error}</p>}

            <div style={styles.grid}>
                {tours.map((tour) => (
                    <div key={tour.id} style={styles.card}>
                        <div style={styles.cardTop}>
                            <h3 style={styles.cardTitle}>{tour.title}</h3>
                            {tour.isHot && <span style={styles.hotBadge}>Гарячий</span>}
                        </div>

                        {tour.description && (
                            <p style={styles.cardDesc}>{tour.description}</p>
                        )}

                        <span style={styles.typePill}>
                            {tourTypeLabels[tour.tourType] || tour.tourType}
                        </span>

                        <div style={styles.cardFooter}>
                            <p style={styles.price}>
                                {tour.basePrice.toLocaleString('uk-UA')}
                                <span style={styles.priceSub}> ₴</span>
                            </p>

                            {/* додаємо обробник події onclick */}
                            <button
                                onClick={() => handleBooking(tour.id, tour.basePrice)}
                                style={styles.bookBtn}
                                onMouseEnter={e => e.target.style.opacity = '0.75'}
                                onMouseLeave={e => e.target.style.opacity = '1'}
                            >
                                Забронювати
                            </button>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}
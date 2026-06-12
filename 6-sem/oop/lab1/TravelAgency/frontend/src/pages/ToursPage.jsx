import { useState, useEffect } from 'react';
import api from '../api/axiosConfig';

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
        <div style={{ maxWidth: '800px', margin: '50px auto', fontFamily: 'sans-serif' }}>
            <h2>Доступні тури</h2>
            {error && <p style={{ color: 'red' }}>{error}</p>}

            <div style={{ display: 'grid', gap: '20px' }}>
                {tours.map((tour) => (
                    <div key={tour.id} style={{ border: '1px solid #ccc', padding: '15px', borderRadius: '8px' }}>
                        <h3>{tour.title} {tour.isHot && <span style={{ color: 'red' }}>🔥 гарячий!</span>}</h3>
                        <p>{tour.description}</p>
                        <p><strong>Тип:</strong> {tour.tourType}</p>
                        <p><strong>Ціна:</strong> {tour.basePrice} ₴</p>

                        {/* додаємо обробник події onclick */}
                        <button
                            onClick={() => handleBooking(tour.id, tour.basePrice)}
                            style={{ padding: '8px 15px', backgroundColor: '#28a745', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' }}>
                            Забронювати
                        </button>
                    </div>
                ))}
            </div>
        </div>
    );
}
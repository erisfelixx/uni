import { useState, useEffect } from 'react';
import api from '../api/axiosConfig';

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
        <div style={{ maxWidth: '800px', margin: '50px auto', fontFamily: 'sans-serif' }}>
            <h2>Мої бронювання</h2>
            {error && <p style={{ color: 'red' }}>{error}</p>}

            {bookings.length === 0 ? (
                <p>У вас ще немає бронювань.</p>
            ) : (
                <div style={{ display: 'grid', gap: '15px' }}>
                    {bookings.map((booking) => (
                        <div key={booking.id} style={{ border: '1px solid #ccc', padding: '15px', borderRadius: '8px', backgroundColor: '#f8f9fa' }}>
                            <p><strong>Номер бронювання:</strong> #{booking.id}</p>
                            <p><strong>ID туру:</strong> {booking.tourId}</p>
                            <p><strong>Статус:</strong> {booking.status}</p>
                            <p><strong>Сплачено:</strong> <span style={{ color: '#28a745', fontWeight: 'bold' }}>{booking.finalPrice} ₴</span></p>
                            <p><strong>Дата створення:</strong> {new Date(booking.createdAt).toLocaleString()}</p>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}
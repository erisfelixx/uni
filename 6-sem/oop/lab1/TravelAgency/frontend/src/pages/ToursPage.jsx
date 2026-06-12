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
                        <button style={{ padding: '8px 15px', backgroundColor: '#28a745', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' }}>
                            Забронювати
                        </button>
                    </div>
                ))}
            </div>
        </div>
    );
}
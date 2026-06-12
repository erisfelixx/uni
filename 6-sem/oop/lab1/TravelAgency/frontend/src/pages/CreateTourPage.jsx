import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../api/axiosConfig';

export default function CreateTourPage() {
    const navigate = useNavigate();

    // початковий стан для нашого нового туру
    const [tour, setTour] = useState({
        title: '',
        description: '',
        tourType: 'REST', // значення за замовчуванням
        basePrice: '',
        isHot: false
    });
    const [message, setMessage] = useState('');
    const [error, setError] = useState('');

    // обробка змін у полях форми
    const handleChange = (e) => {
        const { name, value, type, checked } = e.target;
        setTour({
            ...tour,
            [name]: type === 'checkbox' ? checked : value
        });
    };

    // відправка POST-запиту на бекенд
    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        setMessage('');

        try {
            await api.post('/tours', tour);
            setMessage('тур успішно створено!');

            // очищаємо форму після успішного створення
            setTour({ title: '', description: '', tourType: 'REST', basePrice: '', isHot: false });

            // перенаправляємо на сторінку всіх турів через 2 секунди
            setTimeout(() => navigate('/tours'), 2000);

        } catch (err) {
            setError('помилка створення туру: ' + (err.response?.data?.error || err.message));
        }
    };

    return (
        <div style={{ maxWidth: '500px', margin: '50px auto', fontFamily: 'sans-serif' }}>
            <h2>Створити новий тур</h2>
            {message && <p style={{ color: 'green', fontWeight: 'bold' }}>{message}</p>}
            {error && <p style={{ color: 'red' }}>{error}</p>}

            <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '15px' }}>
                <div>
                    <label>Назва туру:</label><br />
                    <input type="text" name="title" value={tour.title} onChange={handleChange} required style={{ width: '100%', padding: '8px' }} />
                </div>
                <div>
                    <label>Опис:</label><br />
                    <textarea name="description" value={tour.description} onChange={handleChange} rows="4" style={{ width: '100%', padding: '8px' }}></textarea>
                </div>
                <div>
                    <label>Тип туру:</label><br />
                    <select name="tourType" value={tour.tourType} onChange={handleChange} style={{ width: '100%', padding: '8px' }}>
                        <option value="REST">Відпочинок (REST)</option>
                        <option value="EXCURSION">Екскурсія (EXCURSION)</option>
                        <option value="SHOPPING">Шопінг (SHOPPING)</option>
                    </select>
                </div>
                <div>
                    <label>Базова ціна (₴):</label><br />
                    <input type="number" name="basePrice" value={tour.basePrice} onChange={handleChange} required step="0.01" style={{ width: '100%', padding: '8px' }} />
                </div>
                <div>
                    <label style={{ cursor: 'pointer' }}>
                        <input type="checkbox" name="isHot" checked={tour.isHot} onChange={handleChange} style={{ marginRight: '8px' }} />
                        Гарячий тур 🔥
                    </label>
                </div>
                <button type="submit" style={{ padding: '10px', backgroundColor: '#ffc107', color: 'black', border: 'none', borderRadius: '4px', cursor: 'pointer', fontWeight: 'bold' }}>
                    Створити тур
                </button>
            </form>
        </div>
    );
}
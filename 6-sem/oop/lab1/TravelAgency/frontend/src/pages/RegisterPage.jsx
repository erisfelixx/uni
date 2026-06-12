import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import api from '../api/axiosConfig';

export default function RegisterPage() {
    const navigate = useNavigate();

    // стан для полів форми реєстрації
    const [formData, setFormData] = useState({
        fullName: '',
        email: '',
        password: '',
        role: 'CUSTOMER' // за замовчуванням усі нові користувачі — звичайні клієнти
    });

    const [error, setError] = useState('');
    const [message, setMessage] = useState('');

    const handleChange = (e) => {
        setFormData({
            ...formData,
            [e.target.name]: e.target.value
        });
    };

    const handleRegister = async (e) => {
        e.preventDefault();
        setError('');
        setMessage('');

        try {
            // відправляємо запит на створення користувача до backend
            await api.post('/auth/register', formData);
            setMessage('реєстрація успішна! зараз вас буде перенаправлено на сторінку входу...');

            // чекаємо 2 секунди і перекидаємо на логін
            setTimeout(() => navigate('/login'), 2000);

        } catch (err) {
            setError('помилка реєстрації: ' + (err.response?.data?.error || 'невідома помилка'));
        }
    };

    return (
        <div style={{ maxWidth: '400px', margin: '50px auto', fontFamily: 'sans-serif' }}>
            <h2>Реєстрація</h2>
            {message && <p style={{ color: 'green', fontWeight: 'bold' }}>{message}</p>}
            {error && <p style={{ color: 'red' }}>{error}</p>}

            <form onSubmit={handleRegister} style={{ display: 'flex', flexDirection: 'column', gap: '15px' }}>
                <div>
                    <label>Повне ім'я:</label><br />
                    <input
                        type="text"
                        name="fullName"
                        value={formData.fullName}
                        onChange={handleChange}
                        required
                        style={{ width: '100%', padding: '8px' }}
                    />
                </div>
                <div>
                    <label>Email:</label><br />
                    <input
                        type="email"
                        name="email"
                        value={formData.email}
                        onChange={handleChange}
                        required
                        style={{ width: '100%', padding: '8px' }}
                    />
                </div>
                <div>
                    <label>Пароль:</label><br />
                    <input
                        type="password"
                        name="password"
                        value={formData.password}
                        onChange={handleChange}
                        required
                        style={{ width: '100%', padding: '8px' }}
                    />
                </div>
                <button type="submit" style={{ padding: '10px', backgroundColor: '#28a745', color: 'white', border: 'none', cursor: 'pointer', fontWeight: 'bold' }}>
                    Зареєструватися
                </button>
            </form>

            <p style={{ marginTop: '20px', textAlign: 'center' }}>
                Вже є акаунт? <Link to="/login">Увійти</Link>
            </p>
        </div>
    );
}
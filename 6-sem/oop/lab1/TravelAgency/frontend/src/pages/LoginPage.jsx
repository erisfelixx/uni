import { useNavigate, Link } from 'react-router-dom';
import { useState } from 'react';
import api from '../api/axiosConfig';


export default function LoginPage() {
    const navigate = useNavigate();
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');

    const handleLogin = async (e) => {
        e.preventDefault();
        setError('');

        try {
            // відправляємо запит на бекенд
            const response = await api.post('/auth/login', { email, password });

            // зберігаємо токен у пам'ять браузера
            localStorage.setItem('token', response.data.token);
            navigate('/tours');

        } catch (err) {
            // обробка помилки (наприклад, неправильний пароль)
            setError('помилка входу: ' + (err.response?.data?.error || 'невідома помилка'));
        }
    };

    return (
        <div style={{ maxWidth: '400px', margin: '50px auto', fontFamily: 'sans-serif' }}>
            <h2>Вхід до системи</h2>
            {error && <p style={{ color: 'red' }}>{error}</p>}

            <form onSubmit={handleLogin} style={{ display: 'flex', flexDirection: 'column', gap: '15px' }}>
                <div>
                    <label>Email:</label><br />
                    <input
                        type="email"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        required
                        style={{ width: '100%', padding: '8px' }}
                    />
                </div>
                <div>
                    <label>Пароль:</label><br />
                    <input
                        type="password"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        required
                        style={{ width: '100%', padding: '8px' }}
                    />
                </div>
                <button type="submit" style={{ padding: '10px', backgroundColor: '#007bff', color: 'white', border: 'none', cursor: 'pointer' }}>
                    Увійти
                </button>
            </form>
            <p style={{ marginTop: '20px', textAlign: 'center' }}>
                Немає акаунту? <Link to="/register">Зареєструватися</Link>
            </p>
        </div>
    );
}
import { useNavigate, Link } from 'react-router-dom';
import { useState } from 'react';
import api from '../api/axiosConfig';

const styles = {
    page: {
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        fontFamily: "'Inter', sans-serif",
        backgroundColor: '#fafafa',
    },
    card: {
        width: '100%',
        maxWidth: '380px',
        backgroundColor: '#fff',
        border: '0.5px solid rgba(0,0,0,0.12)',
        borderRadius: '12px',
        padding: '2.5rem 2rem',
    },
    title: {
        fontSize: '22px',
        fontWeight: 500,
        margin: '0 0 0.25rem',
        letterSpacing: '-0.01em',
        color: '#1a1a1a',
    },
    subtitle: {
        fontSize: '14px',
        color: '#888',
        margin: '0 0 2rem',
    },
    errorText: {
        fontSize: '13px',
        color: '#A32D2D',
        backgroundColor: '#FAECE7',
        padding: '10px 14px',
        borderRadius: '6px',
        marginBottom: '1.25rem',
    },
    form: {
        display: 'flex',
        flexDirection: 'column',
        gap: '1.25rem',
    },
    field: {
        display: 'flex',
        flexDirection: 'column',
        gap: '6px',
    },
    label: {
        fontSize: '13px',
        fontWeight: 500,
        color: '#444',
    },
    input: {
        padding: '9px 12px',
        fontSize: '14px',
        border: '0.5px solid rgba(0,0,0,0.18)',
        borderRadius: '8px',
        outline: 'none',
        fontFamily: "'Inter', sans-serif",
        color: '#1a1a1a',
        backgroundColor: '#fff',
        transition: 'border-color 0.15s',
    },
    submitBtn: {
        marginTop: '0.5rem',
        padding: '10px',
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
    footer: {
        marginTop: '1.5rem',
        textAlign: 'center',
        fontSize: '13px',
        color: '#888',
    },
    footerLink: {
        color: '#1a1a1a',
        fontWeight: 500,
        textDecoration: 'none',
    },
};

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
        <div style={styles.page}>
            <div style={styles.card}>
                <h2 style={styles.title}>Вхід до системи</h2>
                <p style={styles.subtitle}>Введіть email та пароль для входу</p>

                {error && <p style={styles.errorText}>{error}</p>}

                <form onSubmit={handleLogin} style={styles.form}>
                    <div style={styles.field}>
                        <label style={styles.label}>Email</label>
                        <input
                            type="email"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            required
                            style={styles.input}
                            onFocus={e => e.target.style.borderColor = 'rgba(0,0,0,0.45)'}
                            onBlur={e => e.target.style.borderColor = 'rgba(0,0,0,0.18)'}
                        />
                    </div>

                    <div style={styles.field}>
                        <label style={styles.label}>Пароль</label>
                        <input
                            type="password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            required
                            style={styles.input}
                            onFocus={e => e.target.style.borderColor = 'rgba(0,0,0,0.45)'}
                            onBlur={e => e.target.style.borderColor = 'rgba(0,0,0,0.18)'}
                        />
                    </div>

                    <button
                        type="submit"
                        style={styles.submitBtn}
                        onMouseEnter={e => e.target.style.opacity = '0.75'}
                        onMouseLeave={e => e.target.style.opacity = '1'}
                    >
                        Увійти
                    </button>
                </form>

                <p style={styles.footer}>
                    Немає акаунту?{' '}
                    <Link to="/register" style={styles.footerLink}>Зареєструватися</Link>
                </p>
            </div>
        </div>
    );
}
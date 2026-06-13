import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
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
    successText: {
        fontSize: '13px',
        color: '#1D6A3E',
        backgroundColor: '#E9F7EF',
        padding: '10px 14px',
        borderRadius: '6px',
        marginBottom: '1.25rem',
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
        <div style={styles.page}>
            <div style={styles.card}>
                <h2 style={styles.title}>Реєстрація</h2>
                <p style={styles.subtitle}>Створіть акаунт, щоб бронювати тури</p>

                {message && <p style={styles.successText}>{message}</p>}
                {error && <p style={styles.errorText}>{error}</p>}

                <form onSubmit={handleRegister} style={styles.form}>
                    <div style={styles.field}>
                        <label style={styles.label}>Повне ім'я</label>
                        <input
                            type="text"
                            name="fullName"
                            value={formData.fullName}
                            onChange={handleChange}
                            required
                            style={styles.input}
                            onFocus={e => e.target.style.borderColor = 'rgba(0,0,0,0.45)'}
                            onBlur={e => e.target.style.borderColor = 'rgba(0,0,0,0.18)'}
                        />
                    </div>

                    <div style={styles.field}>
                        <label style={styles.label}>Email</label>
                        <input
                            type="email"
                            name="email"
                            value={formData.email}
                            onChange={handleChange}
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
                            name="password"
                            value={formData.password}
                            onChange={handleChange}
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
                        Зареєструватися
                    </button>
                </form>

                <p style={styles.footer}>
                    Вже є акаунт?{' '}
                    <Link to="/login" style={styles.footerLink}>Увійти</Link>
                </p>
            </div>
        </div>
    );
}
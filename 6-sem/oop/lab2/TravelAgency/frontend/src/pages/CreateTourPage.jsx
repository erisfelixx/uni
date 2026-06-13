import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../api/axiosConfig';

const styles = {
    page: {
        maxWidth: '520px',
        margin: '0 auto',
        padding: '2.5rem 1.25rem',
        fontFamily: "'Inter', sans-serif",
    },
    pageHeader: {
        marginBottom: '2rem',
        paddingBottom: '1rem',
        borderBottom: '0.5px solid rgba(0,0,0,0.12)',
    },
    pageTitle: {
        fontSize: '22px',
        fontWeight: 500,
        margin: 0,
        letterSpacing: '-0.01em',
        color: '#1a1a1a',
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
        width: '100%',
        boxSizing: 'border-box',
    },
    textarea: {
        padding: '9px 12px',
        fontSize: '14px',
        border: '0.5px solid rgba(0,0,0,0.18)',
        borderRadius: '8px',
        outline: 'none',
        fontFamily: "'Inter', sans-serif",
        color: '#1a1a1a',
        backgroundColor: '#fff',
        transition: 'border-color 0.15s',
        width: '100%',
        boxSizing: 'border-box',
        resize: 'vertical',
    },
    select: {
        padding: '9px 12px',
        fontSize: '14px',
        border: '0.5px solid rgba(0,0,0,0.18)',
        borderRadius: '8px',
        outline: 'none',
        fontFamily: "'Inter', sans-serif",
        color: '#1a1a1a',
        backgroundColor: '#fff',
        width: '100%',
        boxSizing: 'border-box',
        cursor: 'pointer',
    },
    checkboxRow: {
        display: 'flex',
        alignItems: 'center',
        gap: '10px',
        cursor: 'pointer',
        userSelect: 'none',
    },
    checkbox: {
        width: '16px',
        height: '16px',
        cursor: 'pointer',
        accentColor: '#1a1a1a',
    },
    checkboxLabel: {
        fontSize: '14px',
        color: '#444',
    },
    divider: {
        border: 'none',
        borderTop: '0.5px solid rgba(0,0,0,0.1)',
        margin: '0.25rem 0',
    },
    submitBtn: {
        marginTop: '0.25rem',
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
};

const focusIn = e => e.target.style.borderColor = 'rgba(0,0,0,0.45)';
const focusOut = e => e.target.style.borderColor = 'rgba(0,0,0,0.18)';

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
        <div style={styles.page}>
            <div style={styles.pageHeader}>
                <h2 style={styles.pageTitle}>Створити новий тур</h2>
            </div>

            {message && <p style={styles.successText}>{message}</p>}
            {error && <p style={styles.errorText}>{error}</p>}

            <form onSubmit={handleSubmit} style={styles.form}>
                <div style={styles.field}>
                    <label style={styles.label}>Назва туру</label>
                    <input
                        type="text"
                        name="title"
                        value={tour.title}
                        onChange={handleChange}
                        required
                        style={styles.input}
                        onFocus={focusIn}
                        onBlur={focusOut}
                    />
                </div>

                <div style={styles.field}>
                    <label style={styles.label}>Опис</label>
                    <textarea
                        name="description"
                        value={tour.description}
                        onChange={handleChange}
                        rows="4"
                        style={styles.textarea}
                        onFocus={focusIn}
                        onBlur={focusOut}
                    />
                </div>

                <div style={styles.field}>
                    <label style={styles.label}>Тип туру</label>
                    <select
                        name="tourType"
                        value={tour.tourType}
                        onChange={handleChange}
                        style={styles.select}
                    >
                        <option value="REST">Відпочинок</option>
                        <option value="EXCURSION">Екскурсія</option>
                        <option value="SHOPPING">Шопінг</option>
                    </select>
                </div>

                <div style={styles.field}>
                    <label style={styles.label}>Базова ціна (₴)</label>
                    <input
                        type="number"
                        name="basePrice"
                        value={tour.basePrice}
                        onChange={handleChange}
                        required
                        step="0.01"
                        style={styles.input}
                        onFocus={focusIn}
                        onBlur={focusOut}
                    />
                </div>

                <hr style={styles.divider} />

                <label style={styles.checkboxRow}>
                    <input
                        type="checkbox"
                        name="isHot"
                        checked={tour.isHot}
                        onChange={handleChange}
                        style={styles.checkbox}
                    />
                    <span style={styles.checkboxLabel}>Гарячий тур</span>
                </label>

                <button
                    type="submit"
                    style={styles.submitBtn}
                    onMouseEnter={e => e.target.style.opacity = '0.75'}
                    onMouseLeave={e => e.target.style.opacity = '1'}
                >
                    Створити тур
                </button>
            </form>
        </div>
    );
}
import { Link, useNavigate } from 'react-router-dom';

const styles = {
    header: {
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        padding: '0 2rem',
        height: '60px',
        backgroundColor: '#fff',
        borderBottom: '0.5px solid rgba(0,0,0,0.12)',
        fontFamily: "'Inter', sans-serif",
    },
    logo: {
        fontSize: '16px',
        fontWeight: 500,
        letterSpacing: '-0.01em',
        color: '#1a1a1a',
        textDecoration: 'none',
    },
    nav: {
        display: 'flex',
        alignItems: 'center',
        gap: '2rem',
    },
    navLink: {
        color: '#555',
        textDecoration: 'none',
        fontSize: '14px',
        fontWeight: 400,
        transition: 'color 0.15s',
    },
    navLinkAccent: {
        color: '#1a1a1a',
        textDecoration: 'none',
        fontSize: '14px',
        fontWeight: 500,
        transition: 'color 0.15s',
    },
    logoutBtn: {
        padding: '6px 16px',
        backgroundColor: 'transparent',
        color: '#888',
        border: '0.5px solid rgba(0,0,0,0.2)',
        borderRadius: '6px',
        fontSize: '14px',
        cursor: 'pointer',
        fontFamily: "'Inter', sans-serif",
        transition: 'all 0.15s',
    },
};

export default function Header() {
    const navigate = useNavigate();

    // дістаємо токен і розшифровуємо роль користувача
    const token = localStorage.getItem('token');
    let userRole = 'CUSTOMER'; // базова роль

    if (token) {
        try {
            const payload = JSON.parse(atob(token.split('.')[1]));
            if (payload.realm_access && payload.realm_access.roles.includes('AGENT')) {
                userRole = 'AGENT';
            }
        } catch (e) {
        }
    }

    // функція для виходу з системи
    const handleLogout = () => {
        localStorage.removeItem('token');
        navigate('/login');
    };

    return (
        <header style={styles.header}>
            <Link to="/tours" style={styles.logo}>TravelAgency</Link>

            <nav style={styles.nav}>
                <Link
                    to="/tours"
                    style={styles.navLink}
                    onMouseEnter={e => e.target.style.color = '#1a1a1a'}
                    onMouseLeave={e => e.target.style.color = '#555'}
                >
                    Всі тури
                </Link>

                <Link
                    to="/my-bookings"
                    style={styles.navLink}
                    onMouseEnter={e => e.target.style.color = '#1a1a1a'}
                    onMouseLeave={e => e.target.style.color = '#555'}
                >
                    Мої бронювання
                </Link>

                {/* показуємо цю кнопку тільки якщо роль AGENT або ADMIN */}
                {(userRole === 'AGENT' || userRole === 'ADMIN') && (
                    <Link
                        to="/create-tour"
                        style={styles.navLinkAccent}
                        onMouseEnter={e => e.target.style.color = '#555'}
                        onMouseLeave={e => e.target.style.color = '#1a1a1a'}
                    >
                        + Створити тур
                    </Link>
                )}

                <button
                    onClick={handleLogout}
                    style={styles.logoutBtn}
                    onMouseEnter={e => { e.target.style.color = '#1a1a1a'; e.target.style.borderColor = 'rgba(0,0,0,0.4)'; }}
                    onMouseLeave={e => { e.target.style.color = '#888'; e.target.style.borderColor = 'rgba(0,0,0,0.2)'; }}
                >
                    Вийти
                </button>
            </nav>
        </header>
    );
}
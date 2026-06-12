import { Link, useNavigate } from 'react-router-dom';

export default function Header() {
    const navigate = useNavigate();

    // дістаємо токен і розшифровуємо роль користувача
    const token = localStorage.getItem('token');
    let userRole = 'CUSTOMER'; // базова роль

    if (token) {
        try {
            const payload = JSON.parse(atob(token.split('.')[1]));
            userRole = payload.role;
        } catch (e) {
            // ігноруємо помилки парсингу
        }
    }

    // функція для виходу з системи
    const handleLogout = () => {
        localStorage.removeItem('token');
        navigate('/login');
    };

    return (
        <header style={{ display: 'flex', justifyContent: 'space-between', padding: '15px 30px', backgroundColor: '#343a40', color: 'white', alignItems: 'center', fontFamily: 'sans-serif' }}>
            <h2 style={{ margin: 0 }}>TravelAgency</h2>
            <nav style={{ display: 'flex', gap: '20px', alignItems: 'center' }}>
                <Link to="/tours" style={{ color: 'white', textDecoration: 'none', fontSize: '18px' }}>Всі тури</Link>
                <Link to="/my-bookings" style={{ color: 'white', textDecoration: 'none', fontSize: '18px' }}>Мої бронювання</Link>

                {/* показуємо цю кнопку тільки якщо роль AGENT або ADMIN */}
                {(userRole === 'AGENT' || userRole === 'ADMIN') && (
                    <Link to="/create-tour" style={{ color: '#ffc107', textDecoration: 'none', fontSize: '18px', fontWeight: 'bold' }}>
                        + Створити тур
                    </Link>
                )}

                <button
                    onClick={handleLogout}
                    style={{ padding: '8px 15px', backgroundColor: '#dc3545', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer', fontWeight: 'bold' }}>
                    Вийти
                </button>
            </nav>
        </header>
    );
}
import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import CreateTourPage from './pages/CreateTourPage';
import LoginPage from './pages/LoginPage';
import ToursPage from './pages/ToursPage';
import MyBookingsPage from './pages/MyBookingsPage';
import Header from './components/Header';
import RegisterPage from './pages/RegisterPage';

const interFont = document.createElement('link');
interFont.rel = 'stylesheet';
interFont.href = 'https://fonts.googleapis.com/css2?family=Inter:wght@400;500&display=swap';
document.head.appendChild(interFont);

// компонент-обгортка для відображення меню
function Layout({ children }) {
    const location = useLocation();
    // не показуємо Header на сторінці логіну
    const showHeader = location.pathname !== '/login' && location.pathname !== '/register';

    return (
        <>
            {showHeader && <Header />}
            {/* padding прибрано — кожна сторінка керує своїми відступами самостійно */}
            <div>
                {children}
            </div>
        </>
    );
}

function App() {
    return (
        <BrowserRouter>
            <Layout>
                <Routes>
                    <Route path="/register" element={<RegisterPage />} />
                    <Route path="/" element={<Navigate to="/login" replace />} />
                    <Route path="/login" element={<LoginPage />} />
                    <Route path="/tours" element={<ToursPage />} />
                    <Route path="/my-bookings" element={<MyBookingsPage />} />
                    <Route path="/create-tour" element={<CreateTourPage />} />
                </Routes>
            </Layout>
        </BrowserRouter>
    );
}

export default App;
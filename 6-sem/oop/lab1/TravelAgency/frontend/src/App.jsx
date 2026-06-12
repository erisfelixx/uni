import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import LoginPage from './pages/LoginPage';
import ToursPage from './pages/ToursPage';

function App() {
    return (
        <BrowserRouter>
            <Routes>
                {/* перенаправляємо з кореневої сторінки на логін */}
                <Route path="/" element={<Navigate to="/login" replace />} />

                <Route path="/login" element={<LoginPage />} />
                <Route path="/tours" element={<ToursPage />} />
            </Routes>
        </BrowserRouter>
    );
}

export default App;
import axios from 'axios';

// створюємо налаштований екземпляр axios
const api = axios.create({
    baseURL: 'http://localhost:8080/TravelAgency/api',
    headers: {
        'Content-Type': 'application/json'
    }
});

// додаємо токен до кожного запиту автоматично (якщо він є у сховищі браузера)
api.interceptors.request.use(
    (config) => {
        const token = localStorage.getItem('token');
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    },
    (error) => Promise.reject(error)
);

export default api;
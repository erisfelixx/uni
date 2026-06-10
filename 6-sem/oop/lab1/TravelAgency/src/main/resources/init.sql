-- 1. Таблиця користувачів (Клієнти та Турагенти)
CREATE TABLE users (
                       id SERIAL PRIMARY KEY,
                       full_name VARCHAR(100) NOT NULL,
                       email VARCHAR(100) UNIQUE NOT NULL,
                       password_hash VARCHAR(255) NOT NULL,
                       role VARCHAR(20) NOT NULL -- Може бути 'CUSTOMER' або 'AGENT'
);

-- 2. Таблиця знижок для постійних клієнтів
CREATE TABLE discounts (
                           id SERIAL PRIMARY KEY,
                           user_id INT REFERENCES users(id) ON DELETE CASCADE,
                           discount_percentage DECIMAL(5,2) NOT NULL CHECK (discount_percentage >= 0 AND discount_percentage <= 100)
);

-- 3. Таблиця турів
CREATE TABLE tours (
                       id SERIAL PRIMARY KEY,
                       title VARCHAR(150) NOT NULL,
                       description TEXT,
                       tour_type VARCHAR(50) NOT NULL, -- 'REST', 'EXCURSION', або 'SHOPPING'
                       base_price DECIMAL(10,2) NOT NULL,
                       is_hot BOOLEAN DEFAULT FALSE
);

-- 4. Таблиця бронювань (Замовлення)
CREATE TABLE bookings (
                          id SERIAL PRIMARY KEY,
                          customer_id INT REFERENCES users(id) ON DELETE CASCADE,
                          tour_id INT REFERENCES tours(id) ON DELETE CASCADE,
                          status VARCHAR(20) NOT NULL DEFAULT 'PENDING', -- 'PENDING', 'PAID', 'CANCELLED'
                          final_price DECIMAL(10,2) NOT NULL,
                          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 5. Таблиця оплат
CREATE TABLE payments (
                          id SERIAL PRIMARY KEY,
                          booking_id INT REFERENCES bookings(id) ON DELETE CASCADE,
                          amount DECIMAL(10,2) NOT NULL,
                          payment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
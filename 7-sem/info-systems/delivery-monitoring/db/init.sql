-- Схема БД служби доставки

-- Кур'єри
CREATE TABLE couriers (
    id         SERIAL PRIMARY KEY,
    name       VARCHAR(100) NOT NULL,
    transport  VARCHAR(20)  NOT NULL          -- bike / car / foot
);

-- Замовлення (поточний стан)
CREATE TABLE orders (
    id            UUID PRIMARY KEY,
    customer      VARCHAR(100) NOT NULL,
    district      VARCHAR(50)  NOT NULL,
    address       VARCHAR(200) NOT NULL,
    price         NUMERIC(10, 2) NOT NULL,
    status        VARCHAR(20)  NOT NULL,      -- created / assigned / picked_up / in_transit / delivered / canceled
    courier_id    INT REFERENCES couriers(id),
    created_at    TIMESTAMPTZ  NOT NULL DEFAULT now(),
    updated_at    TIMESTAMPTZ  NOT NULL DEFAULT now(),
    delivered_at  TIMESTAMPTZ
);

-- Історія подій (кожна зміна статусу)
CREATE TABLE order_events (
    id          BIGSERIAL PRIMARY KEY,
    order_id    UUID NOT NULL REFERENCES orders(id),
    status      VARCHAR(20) NOT NULL,
    courier_id  INT REFERENCES couriers(id),
    event_time  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_orders_status ON orders(status);
CREATE INDEX idx_events_order  ON order_events(order_id);

-- Початкові дані
INSERT INTO couriers (name, transport) VALUES
    ('Олег Коваль', 'car'),   ('Ірина Мельник', 'bike'),
    ('Андрій Бойко', 'foot'), ('Марія Шевчук', 'car'),
    ('Дмитро Ткач', 'bike'),  ('Олена Кравець', 'car'),
    ('Тарас Лисенко', 'bike'),('Наталія Гнатюк', 'foot'),
    ('Сергій Павлюк', 'car'), ('Юлія Савчук', 'bike');
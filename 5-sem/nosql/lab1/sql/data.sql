-- =============================================
-- 1. ОЧИСТКА (TRUNCATE)
TRUNCATE TABLE 
    Order_Status_History, 
    Payments, 
    Order_Items, 
    Orders, 
    Reservations, 
    Loyalty_Program,
    Customer_Feedback,
    Restaurant_Tables, 
    Dish_Recipes,
    Menu_Items, 
    Menu_Categories, 
    Supply_Deliveries,
    Suppliers,
    Ingredients, 
    User_Roles, 
    Users, 
    Work_Shifts,
    Employees, 
    Positions, 
    Roles 
RESTART IDENTITY CASCADE;

-- =============================================
-- 2. НАПОВНЕННЯ ДАНИМИ
-- --- РОЛІ ТА ПОСАДИ ---
INSERT INTO Roles (role_name) VALUES ('Admin'), ('Manager'), ('Waiter'), ('Chef');

INSERT INTO Positions (title, base_salary) VALUES 
('General Manager', 35000.00),
('Head Chef', 30000.00),
('Sous Chef', 20000.00),
('Senior Waiter', 15000.00),
('Junior Waiter', 10000.00);

-- --- ПРАЦІВНИКИ ---
INSERT INTO Employees (first_name, last_name, phone, email, position_id, hire_date) VALUES 
('Іван', 'Петренко', '+380501112233', 'ivan@rest.com', 1, '2023-01-15'),
('Олена', 'Коваль', '+380502223344', 'olena@rest.com', 2, '2023-02-01'),
('Максим', 'Сидоренко', '+380503334455', 'max@rest.com', 4, '2023-03-10'),
('Софія', 'Бондар', '+380504445566', 'sofia@rest.com', 5, '2023-05-20'),
('Андрій', 'Мельник', '+380505556677', 'andriy@rest.com', 3, '2023-04-15');

-- --- ЮЗЕРИ ---
INSERT INTO Users (username, password_hash, employee_id) VALUES 
('admin', 'hash1', 1),
('chef_olena', 'hash2', 2),
('waiter_max', 'hash3', 3),
('waiter_sofia', 'hash4', 4),
('chef_andriy', 'hash5', 5);

INSERT INTO User_Roles (user_id, role_id) VALUES 
(1, 1), (1, 2), 
(2, 4), 
(3, 3), 
(4, 3), 
(5, 4);

-- --- КАТЕГОРІЇ ТА МЕНЮ ---
INSERT INTO Menu_Categories (name) VALUES 
('Перші страви'), ('Основні страви'), ('Салати'), ('Піца'), ('Десерти'), ('Напої');

--  **ID автоінкрементні
INSERT INTO Menu_Items (category_id, name, description, price, weight_grams, updated_by) VALUES 
(1, 'Борщ український', 'З пампушками', 140.00, 350, 2), -- ID 1
(1, 'Курячий бульйон', 'З локшиною', 110.00, 300, 2), -- ID 2
(2, 'Стейк Рібай', 'Яловичина', 550.00, 300, 2), -- ID 3
(2, 'Котлета по-київськи', 'Класика', 220.00, 250, 5), -- ID 4
(3, 'Цезар з куркою', 'Айсберг, курка', 190.00, 250, 2), -- ID 5
(3, 'Грецький салат', 'Фета, оливки', 160.00, 250, 5), -- ID 6
(4, 'Піца Маргарита', 'Моцарела', 200.00, 450, 5), -- ID 7
(4, 'Піца 4 Сири', 'Сирна', 280.00, 450, 5), -- ID 8
(5, 'Чізкейк Нью-Йорк', 'З соусом', 120.00, 150, 2), -- ID 9
(5, 'Тирамісу', 'Італія', 140.00, 160, 2), -- ID 10
(6, 'Капучино', 'Арабіка', 65.00, 200, 1), -- ID 11
(6, 'Лимонад Імбирний', 'Свіжий', 80.00, 400, 1); -- ID 12

-- --- СТОЛИ
INSERT INTO Restaurant_Tables (table_id, table_number, capacity, zone) VALUES 
(1, 1, 4, 'Основний зал'), 
(2, 2, 2, 'Основний зал'), 
(3, 3, 4, 'Основний зал'),
(4, 4, 6, 'Біля вікна'), 
(5, 5, 2, 'Біля вікна'),
(10, 10, 4, 'Тераса'), 
(11, 11, 4, 'Тераса'), 
(12, 12, 8, 'Банкетний зал');

-- оновлюємо лічильник ID столів, щоб наступні INSERT не ламались
SELECT setval('restaurant_tables_table_id_seq', (SELECT MAX(table_id) FROM Restaurant_Tables));

-- --- ІНГРЕДІЄНТИ ---
INSERT INTO Ingredients (name, unit, current_stock, updated_by) VALUES 
('Яловичина', 'кг', 15.0, 2), ('Курка філе', 'кг', 20.0, 2),
('Картопля', 'кг', 60.0, 2), ('Помідори', 'кг', 10.0, 5),
('Огірки', 'кг', 8.0, 5), ('Салат Айсберг', 'кг', 5.0, 5),
('Сир Моцарела', 'кг', 12.0, 5), ('Сир Пармезан', 'кг', 4.0, 2),
('Борошно', 'кг', 30.0, 5), ('Кава зернова', 'кг', 5.0, 1);

-- --- КЛІЄНТИ ---
INSERT INTO Customers (first_name, last_name, phone, email) VALUES 
('Анна', 'Мельник', '+380971112233', 'anna@mail.com'),
('Дмитро', 'Бойко', '+380972223344', 'dima@mail.com'),
('Вікторія', 'Руденко', '+380633334455', 'vika@mail.com'),
('Олег', 'Козак', '+380509998877', 'oleg@mail.com');

-- --- ЗАМОВЛЕННЯ ТА ІСТОРІЯ ---

-- 1. Закрите замовлення (оплачено)
INSERT INTO Orders (table_id, customer_id, waiter_id, status, order_date, total_amount, updated_by) 
VALUES (1, 1, 3, 'Paid', NOW() - INTERVAL '2 hours', 530.00, 3);

INSERT INTO Order_Items (order_id, menu_item_id, quantity, price_at_order) VALUES 
(1, 1, 2, 140.00), 
(1, 5, 1, 190.00), 
(1, 11, 2, 60.00); 

INSERT INTO Payments (order_id, amount, payment_method, payment_date) 
VALUES (1, 530.00, 'Card', NOW() - INTERVAL '1 hour');

INSERT INTO Customer_Feedback (order_id, rating, comment) 
VALUES (1, 5, 'Дуже смачний борщ! Обслуговування на висоті.');


-- 2. Активне замовлення (готується)
INSERT INTO Orders (table_id, customer_id, waiter_id, status, order_date, updated_by) 
VALUES (4, 2, 4, 'Cooking', NOW() - INTERVAL '20 minutes', 4);

INSERT INTO Order_Items (order_id, menu_item_id, quantity, price_at_order) VALUES 
(2, 3, 1, 550.00), 
(2, 7, 1, 200.00), 
(2, 12, 2, 80.00); 


-- 3. Активне замовлення (створено)
INSERT INTO Orders (table_id, customer_id, waiter_id, status, order_date, updated_by) 
VALUES (10, 3, 3, 'Open', NOW() - INTERVAL '5 minutes', 3);

INSERT INTO Order_Items (order_id, menu_item_id, quantity, price_at_order) VALUES 
(3, 9, 1, 120.00), 
(3, 11, 1, 65.00); 


-- 4. Замовлення "Видано"
INSERT INTO Orders (table_id, customer_id, waiter_id, status, order_date, updated_by) 
VALUES (2, 4, 4, 'Served', NOW() - INTERVAL '40 minutes', 4);

INSERT INTO Order_Items (order_id, menu_item_id, quantity, price_at_order) VALUES 
(4, 8, 1, 280.00);
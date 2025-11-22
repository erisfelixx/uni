-- =============================================
-- 1. ЗБЕРЕЖЕНІ ПРОЦЕДУРИ (STORED PROCEDURES)
-- Реалізація бізнес-логіки: м'яке видалення та закриття замовлень
-- =============================================

-- ПРОЦЕДУРА: М'яке видалення страви з меню
-- Замість фізичного видалення (DELETE), ми просто ховаємо страву (is_deleted = TRUE)
CREATE OR REPLACE PROCEDURE sp_soft_delete_menu_item(
    p_item_id INT,
    p_user_id INT
)
LANGUAGE plpgsql
AS $$
BEGIN
    UPDATE Menu_Items
    SET is_deleted = TRUE,
        updated_by = p_user_id
    WHERE item_id = p_item_id;
END;
$$;

-- ПРОЦЕДУРА: Відновлення страви (скасування видалення)
CREATE OR REPLACE PROCEDURE sp_restore_menu_item(
    p_item_id INT,
    p_user_id INT
)
LANGUAGE plpgsql
AS $$
BEGIN
    UPDATE Menu_Items
    SET is_deleted = FALSE,
        updated_by = p_user_id
    WHERE item_id = p_item_id;
END;
$$;

-- ПРОЦЕДУРА: Закриття замовлення (Транзакційна логіка)
-- 1. Рахує фінальну суму.
-- 2. Створює запис про оплату.
-- 3. Оновлює статус замовлення на 'Paid'.
CREATE OR REPLACE PROCEDURE sp_close_order(
    p_order_id INT,
    p_payment_method VARCHAR,
    p_user_id INT
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_total DECIMAL(10,2);
BEGIN
    -- 1. Рахуємо суму замовлення на основі позицій
    SELECT COALESCE(SUM(quantity * price_at_order), 0)
    INTO v_total
    FROM Order_Items
    WHERE order_id = p_order_id;

    -- 2. Фіксуємо оплату
    INSERT INTO Payments (order_id, amount, payment_method, payment_date)
    VALUES (p_order_id, v_total, p_payment_method, NOW());

    -- 3. Закриваємо замовлення
    -- (Це автоматично запустить тригер історії статусів)
    UPDATE Orders
    SET status = 'Paid',
        total_amount = v_total,
        updated_by = p_user_id
    WHERE order_id = p_order_id;
END;
$$;


-- =============================================
-- 2. КОРИСТУВАЦЬКІ ФУНКЦІЇ (FUNCTIONS)
-- Допоміжні обчислення
-- =============================================

-- ФУНКЦІЯ: Отримати поточну суму замовлення
-- Можна використовувати в SELECT запитах або коді
CREATE OR REPLACE FUNCTION fn_get_order_total(p_order_id INT)
RETURNS DECIMAL(10,2)
LANGUAGE plpgsql
AS $$
DECLARE
    v_total DECIMAL(10,2);
BEGIN
    SELECT COALESCE(SUM(quantity * price_at_order), 0)
    INTO v_total
    FROM Order_Items
    WHERE order_id = p_order_id;
    
    RETURN v_total;
END;
$$;


-- =============================================
-- 3. СКЛАДНІ ТРИГЕРИ (COMPLEX TRIGGERS)
-- Автоматизація та захист даних
-- =============================================

-- ТРИГЕРНА ФУНКЦІЯ: Логування історії статусів
-- Якщо статус замовлення змінюється (наприклад, Open -> Cooking), записуємо це в історію
CREATE OR REPLACE FUNCTION log_order_status_change()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF (OLD.status IS DISTINCT FROM NEW.status) THEN
        INSERT INTO Order_Status_History (
            order_id, 
            status_from, 
            status_to, 
            changed_by, 
            changed_at
        )
        VALUES (
            NEW.order_id, 
            OLD.status, 
            NEW.status, 
            NEW.updated_by, 
            NOW()
        );
    END IF;
    RETURN NEW;
END;
$$;

-- Прив'язка тригера до таблиці Orders
CREATE OR REPLACE TRIGGER trg_log_order_status
AFTER UPDATE ON Orders
FOR EACH ROW
EXECUTE FUNCTION log_order_status_change();


-- ТРИГЕРНА ФУНКЦІЯ: Захист активних столів
-- Забороняє видаляти стіл, якщо за ним є відкриті замовлення
CREATE OR REPLACE FUNCTION prevent_delete_active_table()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    active_orders_count INT;
BEGIN
    SELECT COUNT(*) INTO active_orders_count
    FROM Orders
    WHERE table_id = OLD.table_id AND status IN ('Open', 'Cooking', 'Served');

    IF active_orders_count > 0 THEN
        RAISE EXCEPTION 'Не можна видалити стіл ID %, тому що за ним є % активних замовлень.', OLD.table_id, active_orders_count;
    END IF;

    RETURN OLD;
END;
$$;

-- Прив'язка тригера до таблиці Restaurant_Tables
CREATE OR REPLACE TRIGGER trg_prevent_table_delete
BEFORE DELETE ON Restaurant_Tables
FOR EACH ROW
EXECUTE FUNCTION prevent_delete_active_table();


-- =============================================
-- 4. РОЗРІЗИ ДАНИХ (VIEWS)
-- Зручне відображення інформації (Repository helper)
-- =============================================

-- VIEW: Активне меню
-- Показує тільки ті страви, які не видалені (Soft Delete) + назви категорій
CREATE OR REPLACE VIEW v_active_menu_items AS
SELECT 
    mi.item_id,
    mi.name AS dish_name,
    mc.name AS category,
    mi.price,
    mi.description
FROM Menu_Items mi
JOIN Menu_Categories mc ON mi.category_id = mc.category_id
WHERE mi.is_deleted = FALSE;

-- VIEW: Ефективність офіціантів
-- Показує кількість закритих замовлень та суму продажів по кожному офіціанту
CREATE OR REPLACE VIEW v_waiter_performance AS
SELECT 
    e.first_name || ' ' || e.last_name AS waiter_name,
    COUNT(o.order_id) AS orders_count,
    COALESCE(SUM(o.total_amount), 0) AS total_sales
FROM Employees e
LEFT JOIN Orders o ON e.employee_id = o.waiter_id
WHERE o.status = 'Paid'
GROUP BY e.employee_id, e.first_name, e.last_name;

-- VIEW: Повні деталі замовлень
-- Збирає до купи дані про клієнта, столик та статус для адмін-панелі

CREATE OR REPLACE VIEW v_order_details_full AS
SELECT 
    o.order_id,
    o.order_date,
    o.status,
    t.table_number,
    c.first_name || ' ' || c.last_name AS customer_name,
    e.first_name || ' ' || e.last_name AS waiter_name,
    
    (
        SELECT STRING_AGG(mi.name || ' (' || oi.quantity || ' шт.)', ', ')
        FROM Order_Items oi
        JOIN Menu_Items mi ON oi.menu_item_id = mi.item_id
        WHERE oi.order_id = o.order_id
    ) AS ordered_items,

    COALESCE(o.total_amount, fn_get_order_total(o.order_id)) AS total_amount

FROM Orders o
JOIN Restaurant_Tables t ON o.table_id = t.table_id
LEFT JOIN Customers c ON o.customer_id = c.customer_id
JOIN Employees e ON o.waiter_id = e.employee_id;
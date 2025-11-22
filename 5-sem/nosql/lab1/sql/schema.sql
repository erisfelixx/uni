--функція для автоматичного оновлення поля updated_at
CREATE OR REPLACE FUNCTION update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
   NEW.updated_at = NOW();
   RETURN NEW;
END;
$$ LANGUAGE plpgsql;



--таблиці:

CREATE TABLE Positions (
    position_id SERIAL PRIMARY KEY,
    title VARCHAR(100) NOT NULL,
    base_salary DECIMAL(10,2) NOT NULL
);

CREATE TABLE Employees (
    employee_id SERIAL PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    phone VARCHAR(20),
    email VARCHAR(100),
    position_id INT REFERENCES Positions(position_id),
    hire_date DATE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE,
    updated_by INT
);

CREATE TABLE Users (
    user_id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    employee_id INT REFERENCES Employees(employee_id), 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

--посилання updated_by в Employees
ALTER TABLE Employees ADD CONSTRAINT fk_employees_updated_by FOREIGN KEY (updated_by) REFERENCES Users(user_id);

CREATE TABLE Roles (
    role_id SERIAL PRIMARY KEY,
    role_name VARCHAR(50) UNIQUE NOT NULL
);

CREATE TABLE User_Roles (
    user_id INT REFERENCES Users(user_id),
    role_id INT REFERENCES Roles(role_id),
    PRIMARY KEY (user_id, role_id)
);

CREATE TABLE Work_Shifts (
    shift_id SERIAL PRIMARY KEY,
    employee_id INT REFERENCES Employees(employee_id),
    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    end_time TIMESTAMP WITH TIME ZONE NOT NULL
);






CREATE TABLE Menu_Categories (
    category_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL
);

CREATE TABLE Menu_Items (
    item_id SERIAL PRIMARY KEY,
    category_id INT REFERENCES Menu_Categories(category_id),
    name VARCHAR(150) NOT NULL,
    description TEXT,
    price DECIMAL(10,2) NOT NULL,
    weight_grams INT,
    is_deleted BOOLEAN DEFAULT FALSE, -- soft delete
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE,
    updated_by INT REFERENCES Users(user_id)
);

CREATE TABLE Ingredients (
    ingredient_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    unit VARCHAR(20) NOT NULL,
    current_stock DECIMAL(10,3) DEFAULT 0,
    updated_at TIMESTAMP WITH TIME ZONE,
    updated_by INT REFERENCES Users(user_id)
);

CREATE TABLE Dish_Recipes (
    recipe_id SERIAL PRIMARY KEY,
    menu_item_id INT REFERENCES Menu_Items(item_id),
    ingredient_id INT REFERENCES Ingredients(ingredient_id),
    quantity_required DECIMAL(10,3) NOT NULL
);

CREATE TABLE Suppliers (
    supplier_id SERIAL PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    contact_info VARCHAR(255),
    is_deleted BOOLEAN DEFAULT FALSE
);

CREATE TABLE Supply_Deliveries (
    delivery_id SERIAL PRIMARY KEY,
    supplier_id INT REFERENCES Suppliers(supplier_id),
    delivery_date DATE NOT NULL,
    total_amount DECIMAL(10,2),
    received_by INT REFERENCES Employees(employee_id)
);






CREATE TABLE Restaurant_Tables (
    table_id SERIAL PRIMARY KEY,
    table_number INT UNIQUE NOT NULL,
    capacity INT NOT NULL,
    zone VARCHAR(50)
);

CREATE TABLE Customers (
    customer_id SERIAL PRIMARY KEY,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    phone VARCHAR(20) UNIQUE,
    email VARCHAR(100),
    is_deleted BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE,
    updated_by INT REFERENCES Users(user_id)
);

CREATE TABLE Reservations (
    reservation_id SERIAL PRIMARY KEY,
    customer_id INT REFERENCES Customers(customer_id),
    table_id INT REFERENCES Restaurant_Tables(table_id),
    reservation_time TIMESTAMP WITH TIME ZONE NOT NULL,
    guest_count INT,
    status VARCHAR(50) DEFAULT 'confirmed',
    is_deleted BOOLEAN DEFAULT FALSE
);

CREATE TABLE Orders (
    order_id SERIAL PRIMARY KEY,
    table_id INT REFERENCES Restaurant_Tables(table_id),
    customer_id INT REFERENCES Customers(customer_id),
    waiter_id INT REFERENCES Employees(employee_id),
    order_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    status VARCHAR(50) NOT NULL,
    total_amount DECIMAL(10,2),
    updated_at TIMESTAMP WITH TIME ZONE,
    updated_by INT REFERENCES Users(user_id)
);

CREATE TABLE Order_Items (
    order_item_id SERIAL PRIMARY KEY,
    order_id INT REFERENCES Orders(order_id),
    menu_item_id INT REFERENCES Menu_Items(item_id),
    quantity INT NOT NULL,
    price_at_order DECIMAL(10,2) NOT NULL,
    notes TEXT
);

CREATE TABLE Payments (
    payment_id SERIAL PRIMARY KEY,
    order_id INT REFERENCES Orders(order_id),
    amount DECIMAL(10,2) NOT NULL,
    payment_method VARCHAR(50),
    payment_date TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);





CREATE TABLE Promotions (
    promotion_id SERIAL PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    discount_percentage DECIMAL(5,2),
    start_date DATE,
    end_date DATE,
    is_active BOOLEAN DEFAULT TRUE
);

CREATE TABLE Loyalty_Program (
    loyalty_id SERIAL PRIMARY KEY,
    customer_id INT UNIQUE REFERENCES Customers(customer_id),
    points_balance INT DEFAULT 0,
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE Customer_Feedback (
    feedback_id SERIAL PRIMARY KEY,
    order_id INT REFERENCES Orders(order_id),
    rating INT NOT NULL, -- 1-5
    comment TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE Order_Status_History (
    history_id SERIAL PRIMARY KEY,
    order_id INT REFERENCES Orders(order_id),
    status_from VARCHAR(50),
    status_to VARCHAR(50) NOT NULL,
    changed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    changed_by INT REFERENCES Users(user_id)
);

-- тригери для авто-оновлення updated_at

CREATE TRIGGER trigger_employees_update BEFORE UPDATE ON Employees FOR EACH ROW EXECUTE FUNCTION update_timestamp();
CREATE TRIGGER trigger_menu_items_update BEFORE UPDATE ON Menu_Items FOR EACH ROW EXECUTE FUNCTION update_timestamp();
CREATE TRIGGER trigger_ingredients_update BEFORE UPDATE ON Ingredients FOR EACH ROW EXECUTE FUNCTION update_timestamp();
CREATE TRIGGER trigger_customers_update BEFORE UPDATE ON Customers FOR EACH ROW EXECUTE FUNCTION update_timestamp();
CREATE TRIGGER trigger_orders_update BEFORE UPDATE ON Orders FOR EACH ROW EXECUTE FUNCTION update_timestamp();

-- індекси:
-- B-Tree індекси (для пошуку)
CREATE INDEX idx_customers_phone ON Customers(phone);
CREATE INDEX idx_orders_date ON Orders(order_date);
CREATE INDEX idx_menu_items_name ON Menu_Items(name);

-- Partial Index (для активних записів)
CREATE INDEX idx_active_menu_items ON Menu_Items(item_id) WHERE is_deleted = FALSE;
CREATE INDEX idx_open_orders ON Orders(order_id) WHERE status = 'Open';

-- GIN індекс (для пошку по описах страв/ по відгуках)
CREATE INDEX idx_menu_description_search ON Menu_Items USING GIN (to_tsvector('english', description));
CREATE INDEX idx_feedback_search ON Customer_Feedback USING GIN (to_tsvector('english', comment));
from restaurant.repositories.base_repository import BaseRepository
import psycopg2.extras

class OrderRepository(BaseRepository):
    # читання: використовуємо View v_order_details_full
    def get_all_orders_report(self):
        with self.connection.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
            cursor.execute("SELECT * FROM v_order_details_full;")
            return cursor.fetchall()

    # зміна: процедура sp_close_order
    def close_order(self, order_id, payment_method, user_id):
        with self.connection.cursor() as cursor:
            cursor.execute("CALL sp_close_order(%s, %s, %s);", (order_id, payment_method, user_id))

    def get_order_full_data(self, order_id):
        """
        Отримує повні дані про замовлення для архівації.
        Повертає словник (dict), готовий для MongoDB.
        """
        with self.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
            # 1. Отримуємо шапку замовлення
            cursor.execute("""
                SELECT o.order_id, o.order_date, o.total_amount, o.status, 
                       t.table_number, 
                       c.first_name || ' ' || c.last_name as customer_name,
                       e.first_name || ' ' || e.last_name as waiter_name
                FROM Orders o
                JOIN Restaurant_Tables t ON o.table_id = t.table_id
                LEFT JOIN Customers c ON o.customer_id = c.customer_id
                JOIN Employees e ON o.waiter_id = e.employee_id
                WHERE o.order_id = %s;
            """, (order_id,))
            order = cursor.fetchone()
            
            if not order:
                return None

            # 2. Отримуємо список товарів
            cursor.execute("""
                SELECT mi.name, oi.quantity, oi.price_at_order
                FROM Order_Items oi
                JOIN Menu_Items mi ON oi.menu_item_id = mi.item_id
                WHERE oi.order_id = %s;
            """, (order_id,))
            items = cursor.fetchall()
            
            # 3. Вкладаємо товари всередину об'єкта замовлення
            order['items'] = [dict(item) for item in items]
            
            # Конвертуємо дату в рядок (Mongo драйвер сам вміє datetime, але RealDictCursor може дати специфічний тип)
            # Для простоти залишимо як є, pymongo впорається з datetime
            
            return dict(order)
        
    
    def create_order(self, table_id, customer_id, waiter_id, items):
        """
        Створює замовлення в SQL (розкладає дані по таблицях).
        items - це список словників [{'menu_item_id': 1, 'quantity': 2, 'price': 120}, ...]
        """
        with self.connection.cursor() as cursor:
            # 1. Створюємо шапку замовлення (Orders)
            cursor.execute("""
                INSERT INTO Orders (table_id, customer_id, waiter_id, status, order_date)
                VALUES (%s, %s, %s, 'Open', NOW())
                RETURNING order_id;
            """, (table_id, customer_id, waiter_id))
            
            new_order_id = cursor.fetchone()[0]

            # 2. Додаємо кожну страву окремо (Order_Items)
            # Це і є "ціна" нормалізації - багато запитів замість одного
            for item in items:
                cursor.execute("""
                    INSERT INTO Order_Items (order_id, menu_item_id, quantity, price_at_order)
                    VALUES (%s, %s, %s, %s);
                """, (new_order_id, item['menu_item_id'], item['quantity'], item['price']))
            
            return new_order_id    
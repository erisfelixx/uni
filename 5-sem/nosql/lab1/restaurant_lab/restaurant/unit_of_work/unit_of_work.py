import os
from pymongo import MongoClient
from restaurant.database.connection import get_db_connection
from restaurant.repositories.menu_repository import MenuRepository
from restaurant.repositories.order_repository import OrderRepository
# Додали імпорт нового репозиторію
from restaurant.repositories.orders_archive_repository import OrdersArchiveRepository

class UnitOfWork:
    def __init__(self):
        self.pg_conn = None
        self.mongo_client = None

    def __enter__(self):
        # 1. Підключення до PostgreSQL
        self.pg_conn = get_db_connection()
        self.pg_conn.autocommit = False 
        
        # 2. Підключення до MongoDB (URL з environment або дефолтний)
        mongo_url = os.getenv("MONGO_URL", "mongodb://localhost:27017/")
        self.mongo_client = MongoClient(mongo_url)

        # 3. Ініціалізація репозиторіїв
        self.menu = MenuRepository(self.pg_conn)
        self.orders = OrderRepository(self.pg_conn)
        
        # Новий репозиторій отримує клієнт Mongo
        self.orders_archive = OrdersArchiveRepository(self.mongo_client)
        
        return self

    def __exit__(self, exc_type, exc_val, traceback):
        # Логіка транзакції стосується переважно SQL
        if exc_type is not None:
            self.pg_conn.rollback()
            print(f"Transaction rolled back due to: {exc_val}")
        else:
            self.pg_conn.commit()
        
        # Закриваємо обидва з'єднання
        if self.pg_conn:
            self.pg_conn.close()
        if self.mongo_client:
            self.mongo_client.close()
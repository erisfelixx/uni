from restaurant.database.connection import get_db_connection
from restaurant.repositories.menu_repository import MenuRepository
from restaurant.repositories.order_repository import OrderRepository

class UnitOfWork:
    def __init__(self):
        self.connection = None

    def __enter__(self):
        self.connection = get_db_connection()
        self.connection.autocommit = False  #ручне управління транзакціями
        
        self.menu = MenuRepository(self.connection)
        self.orders = OrderRepository(self.connection)
        
        return self

    def __exit__(self, exc_type, exc_val, traceback):
        if exc_type is not None:
            self.connection.rollback() #на випадок помилки
            print(f"Transaction rolled back due to: {exc_val}")
        else:
            self.connection.commit()   #успіх - зберігаємо
        
        self.connection.close()
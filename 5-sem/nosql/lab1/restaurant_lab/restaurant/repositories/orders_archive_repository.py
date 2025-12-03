from pymongo import MongoClient
from datetime import datetime

class OrdersArchiveRepository:
    def __init__(self, mongo_client):
        self.collection = mongo_client["restaurant_db"]["orders_archive"]

    def archive_order(self, order_data):
        """
        Зберігає замовлення в MongoDB як один документ.
        Ми очікуємо, що order_data - це вже готовий словник (JSON).
        """
        # Додаємо час архівації
        order_data["archived_at"] = datetime.now()
        
        # Вставляємо в колекцію
        result = self.collection.insert_one(order_data)
        return result.inserted_id

    def get_order_history(self, limit=5):
        """Отримати останні архівовані замовлення"""
        return list(self.collection.find().sort("archived_at", -1).limit(limit))
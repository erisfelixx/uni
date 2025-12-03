import redis
import fakeredis 
import json

# ==========================================
# 1. РЕПОЗИТОРІЙ КОШИКА (Key-Value Logic)
# ==========================================
class CartRepository:
    def __init__(self):
        self.r = fakeredis.FakeRedis(decode_responses=True)

    def add_item(self, session_id, item_id, name, price, quantity):
        """
        Додає товар у кошик.
        У Redis кошик буде зберігатися як HASH (словник):
        Ключ: "cart:{session_id}"
        Поля: item_id -> JSON з даними про товар
        """
        cart_key = f"cart:{session_id}"
        
        # Формуємо дані про товар
        item_data = {
            "name": name,
            "price": price,
            "quantity": quantity
        }
        
        self.r.hset(cart_key, item_id, json.dumps(item_data))
        
        # Встановлюємо "час життя" кошика (TTL) - 1 година
        # Якщо користувач нічого не робить, кошик сам видалиться
        self.r.expire(cart_key, 3600)
        
        print(f"[Redis] Додано '{name}' у кошик користувача {session_id}")

    def get_cart(self, session_id):
        """Отримує всі товари з кошика"""
        cart_key = f"cart:{session_id}"
        
        # Отримуємо всі поля хешу (hgetall)
        raw_items = self.r.hgetall(cart_key)
        
        cart_items = []
        total_price = 0
        
        for item_id, item_json in raw_items.items():
            data = json.loads(item_json)
            cost = data['price'] * data['quantity']
            total_price += cost
            
            cart_items.append({
                "id": item_id,
                "name": data['name'],
                "qty": data['quantity'],
                "cost": cost
            })
            
        return cart_items, total_price

    def clear_cart(self, session_id):
        """Очищає кошик"""
        cart_key = f"cart:{session_id}"
        self.r.delete(cart_key)
        print(f"[Redis] Кошик {session_id} очищено.")

# ==========================================
# 2. ДЕМОНСТРАЦІЯ
# ==========================================
if __name__ == "__main__":
    print("--- REDIS SHOPPING CART DEMO ---\n")
    
    cart = CartRepository()
    user_session = "session_12345" # Умовний ID сесії користувача на сайті

    # 1. Додаємо товари
    cart.add_item(user_session, "item_1", "Борщ", 140.00, 2)
    cart.add_item(user_session, "item_5", "Тірамісу", 140.00, 1)
    
    # 2. Дивимось кошик
    print(f"\nПерегляд кошика для {user_session}:")
    items, total = cart.get_cart(user_session)
    
    for i in items:
        print(f" - {i['name']} (x{i['qty']}) = {i['cost']} грн")
    print(f"РАЗОМ: {total} грн\n")

    # 3. Очищаємо
    cart.clear_cart(user_session)
    
    # 4. Перевіряємо, що пусто
    items, _ = cart.get_cart(user_session)
    if not items:
        print("Кошик порожній.")
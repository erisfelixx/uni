from restaurant.unit_of_work.unit_of_work import UnitOfWork
import time
from decimal import Decimal

def convert_decimals(obj):
    """Рекурсивно конвертує Decimal у float для сумісності з MongoDB"""
    if isinstance(obj, list):
        return [convert_decimals(i) for i in obj]
    elif isinstance(obj, dict):
        return {k: convert_decimals(v) for k, v in obj.items()}
    elif isinstance(obj, Decimal):
        return float(obj)
    return obj

def show_mongo_archive():
    print("\n--- АРХІВ ЗАМОВЛЕНЬ (з MongoDB) ---")
    with UnitOfWork() as uow:
        history = uow.orders_archive.get_order_history()
        if not history:
            print("Архів порожній.")
        for doc in history:
            print(f"Mongo ID: {doc['_id']}")
            print(f"Замовлення #{doc['order_id']} від {doc['order_date']}")
            print(f"Клієнт: {doc['customer_name']} | Сума: {doc['total_amount']}")
            print("Товари:")
            for item in doc['items']:
                print(f" - {item['name']} x{item['quantity']} ({item['price_at_order']} грн)")
            print("-" * 30)

def process_checkout_and_archive(order_id_to_close):
    print(f"\n--- ПРОЦЕС: Закриття та Архівація замовлення #{order_id_to_close} ---")
    
    with UnitOfWork() as uow:
        # 1. SQL: Закриваємо замовлення (рахуємо суму, ставимо статус Paid)
        print(f"[PostgreSQL] Закриваємо замовлення...")
        uow.orders.close_order(order_id=order_id_to_close, payment_method='Card', user_id=1)
        
        # 2. SQL: Витягуємо повні дані (вже з порахованою сумою)
        print(f"[PostgreSQL] Отримуємо дані для міграції...")
        full_order_data = uow.orders.get_order_full_data(order_id_to_close)
        
        if full_order_data:
            # КОНВЕРТАЦІЯ: Перетворюємо Decimal -> float
            full_order_data = convert_decimals(full_order_data)

            # 3. MongoDB: Зберігаємо документ
            print(f"[MongoDB] Архівуємо документ...")
            mongo_id = uow.orders_archive.archive_order(full_order_data)
            print(f"Успішно архівовано! Mongo ID: {mongo_id}")
        else:
            print("Помилка: Замовлення не знайдено!")

if __name__ == "__main__":
    # 1. Дивимось, що в архіві пусто
    show_mongo_archive()

    # 2. Виконуємо операцію (Закриваємо замовлення №3)
    try:
        process_checkout_and_archive(3)
    except Exception as e:
        print(f"Сталася помилка: {e}")

    # 3. Перевіряємо архів знову
    show_mongo_archive()
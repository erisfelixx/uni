import time
from restaurant.unit_of_work.unit_of_work import UnitOfWork

# Кількість замовлень для тесту
ITERATIONS = 1000

def benchmark_sql_write():
    print(f"--- SQL Benchmark: Creating {ITERATIONS} orders ---")
    start_time = time.time()
    
    with UnitOfWork() as uow:
        # Створюємо 1000 замовлень
        for _ in range(ITERATIONS):
            # Імітація даних замовлення (3 страви)
            items = [
                {'menu_item_id': 1, 'quantity': 1, 'price': 140.00},
                {'menu_item_id': 2, 'quantity': 1, 'price': 550.00},
                {'menu_item_id': 11, 'quantity': 2, 'price': 65.00}
            ]
            # Викликаємо наш метод, який робить INSERT в Orders і Order_Items
            uow.orders.create_order(table_id=1, customer_id=1, waiter_id=3, items=items)
        
        # Комітимо всі зміни разом (щоб було чесно, вимірюємо чистий час вставки)
        # У реальності коміт може бути після кожного, що ще більше сповільнить SQL
        uow.pg_conn.commit() # Для SQL це важливо

    duration = time.time() - start_time
    print(f"SQL Time: {duration:.4f} seconds")
    return duration

def benchmark_mongo_write():
    print(f"\n--- MongoDB Benchmark: Inserting {ITERATIONS} documents ---")
    start_time = time.time()
    
    with UnitOfWork() as uow:
        for i in range(ITERATIONS):
            # Та ж сама структура даних, але одним шматком (JSON)
            order_doc = {
                "table_number": 1,
                "customer_id": 1,
                "waiter_id": 3,
                "status": "Open",
                "items": [
                    {"name": "Борщ", "quantity": 1, "price": 140.00},
                    {"name": "Стейк", "quantity": 1, "price": 550.00},
                    {"name": "Капучино", "quantity": 2, "price": 65.00}
                ],
                "total_amount": 820.00,
                "benchmark_id": i # Щоб потім легко знайти/видалити
            }
            # Вставка одного документа
            uow.orders_archive.archive_order(order_doc)

    duration = time.time() - start_time
    print(f"MongoDB Time: {duration:.4f} seconds")
    return duration

if __name__ == "__main__":
    print("Starting Benchmark...\n")
    
    sql_time = benchmark_sql_write()
    mongo_time = benchmark_mongo_write()
    
    print("\n" + "="*30)
    print("RESULTS:")
    print(f"SQL Average: {sql_time/ITERATIONS:.5f} sec/op")
    print(f"Mongo Average: {mongo_time/ITERATIONS:.5f} sec/op")
    
    ratio = sql_time / mongo_time
    print(f"\nMongoDB was {ratio:.2f}x times faster than PostgreSQL")
    print("="*30)
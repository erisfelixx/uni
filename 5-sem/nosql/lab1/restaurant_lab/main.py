from restaurant.unit_of_work.unit_of_work import UnitOfWork

def show_menu():
    print("\n--- АКТИВНЕ МЕНЮ (з View) ---")
    with UnitOfWork() as uow:
        items = uow.menu.get_active_menu()
        for item in items:
            print(f"[{item['item_id']}] {item['dish_name']} - {item['price']} грн ({item['category']})")

def show_orders():
    print("\n--- ЗВІТ ПО ЗАМОВЛЕННЯХ (з View) ---")
    with UnitOfWork() as uow:
        orders = uow.orders.get_all_orders_report()
        for o in orders:
            print(f"Замовлення #{o['order_id']} | Стіл {o['table_number']} | Статус: {o['status']} | Сума: {o['total_amount']}")
            print(f"   Страви: {o['ordered_items']}")
            print("-" * 40)

def demo_transaction():
    print("\n--- ДЕМОНСТРАЦІЯ ТРАНЗАКЦІЇ ---")
    # сценарій:адмін вирішив видалити страву з меню і закрити замовленнч
    try:
        with UnitOfWork() as uow:
            print("1. Видаляємо 'Лимонад Імбирний' (ID 12) з меню...")
            uow.menu.soft_delete_item(item_id=12, user_id=1)
            
            print("2. Закриваємо замовлення #4 (Оплата готівкою)...")
            uow.orders.close_order(order_id=4, payment_method='Cash', user_id=1)
            
            # автоматичний коміт
            print("Транзакція успішно завершена!")
            
    except Exception as e:
        print(f"Помилка! Транзакцію скасовано.")

if __name__ == "__main__":
    # 1. показуємо початковий стан
    show_menu()
    show_orders()

    # 2. пиконуємо зміни
    demo_transaction()

    # 3. показуємо результат
    show_menu()
    show_orders()
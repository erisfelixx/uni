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
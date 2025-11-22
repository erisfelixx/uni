from restaurant.repositories.base_repository import BaseRepository
import psycopg2.extras

class MenuRepository(BaseRepository):
    # читання: використовуємо View v_active_menu_items
    def get_active_menu(self):
        with self.connection.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
            cursor.execute("SELECT * FROM v_active_menu_items;")
            return cursor.fetchall()

    # зміна: процедура sp_soft_delete_menu_item
    def soft_delete_item(self, item_id, user_id):
        with self.connection.cursor() as cursor:
            cursor.execute("CALL sp_soft_delete_menu_item(%s, %s);", (item_id, user_id))
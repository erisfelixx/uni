import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

public class MD4Test {

    @Test
    public void testRfc1320Vectors() {
        // офіційні тестові вектори зі специфікації RFC 1320
        assertEquals("31d6cfe0d16ae931b73c59d7e0c089c0", MD4.hashHex(""), "Хеш порожнього рядка не збігається");
        assertEquals("bde52cb31de33e46245e05fbdbd6fb24", MD4.hashHex("a"), "Хеш для 'a' не збігається");
        assertEquals("a448017aaf21d8525fc10ae87aa6729d", MD4.hashHex("abc"), "Хеш для 'abc' не збігається");
        assertEquals("d9130a8164549fe818874806e1c7014b", MD4.hashHex("message digest"), "Хеш для 'message digest' не збігається");
        assertEquals("d79e1c308aa5bbcdeea8ed63df412da9", MD4.hashHex("abcdefghijklmnopqrstuvwxyz"), "Хеш для алфавіту не збігається");
    }

    @Test
    public void testLongString() {
        // довгий рядок для перевірки розбиття повідомлення на кілька блоків
        String input = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";
        String expected = "043f8582f241db351ce627e153e7f0e4";
        assertEquals(expected, MD4.hashHex(input), "Хеш довгого рядка обчислено некоректно");
    }

    @Test
    public void testUtf8Characters() {
        // перевірка підтримки не-ASCII символів (кирилиця)
        String input = "Тестове повідомлення";
        String hash = MD4.hashHex(input);
        
        assertNotNull(hash, "Хеш не має бути null");
        assertEquals(32, hash.length(), "Довжина хешу MD4 завжди має складати 32 символи");
        assertTrue(hash.matches("^[a-f0-9]{32}$"), "Хеш має містити лише шістнадцяткові символи у нижньому регістрі");
    }

    @Test
    public void testNullInput() {
        // перевірка стійкості методу до передачі null-значень
        Exception exception = assertThrows(NullPointerException.class, () -> {
            MD4.hashHex(null);
        });
        assertNotNull(exception, "Очікується NullPointerException, оскільки метод не розрахований на null");
    }
}
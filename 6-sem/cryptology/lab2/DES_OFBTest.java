import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

public class DES_OFBTest {

    // константи для тестування (взяті з Main.java)
    private static final long DEFAULT_KEY = 0x133457799BBCDFF1L;
    private static final long DEFAULT_IV = 0xABCDEF1234567890L;

    @Test
    public void testKnownVectors() {
        DES_OFB cipher = new DES_OFB(DEFAULT_KEY);
        
        // перевірка 1: Короткий рядок (< 1 блоку)
        byte[] enc1 = cipher.encrypt("Hello!", DEFAULT_IV);
        assertEquals("d97e5736bf86", DES_OFB.toHex(enc1), "Шифротекст для 'Hello!' не збігається з очікуваним вектором");
        
        // перевірка 2: Довгий рядок (> 1 блоку)
        byte[] enc2 = cipher.encrypt("Today is sunny.", DEFAULT_IV);
        assertEquals("c5745f3ba9872447f99c0adfc29b16", DES_OFB.toHex(enc2), "Шифротекст для довгого рядка не збігається");
    }

    @Test
    public void testSymmetryOfOfbMode() {
        // у режимі OFB операція шифрування та розшифрування ідентична (XOR)
        DES_OFB cipher = new DES_OFB(DEFAULT_KEY);
        String originalText = "Криптографія - це дуже цікаво! 123";
        
        byte[] encrypted = cipher.encrypt(originalText, DEFAULT_IV);
        String decrypted = cipher.decrypt(encrypted, DEFAULT_IV);
        
        assertEquals(originalText, decrypted, "Розшифрований текст має повністю збігатися з оригіналом");
    }

    @Test
    public void testIvInfluence() {
        // перевірка того, що різні ініціалізаційні вектори (IV) генерують різний keystream
        DES_OFB cipher = new DES_OFB(DEFAULT_KEY);
        String text = "Secret Message";
        
        byte[] enc1 = cipher.encrypt(text, DEFAULT_IV);
        byte[] enc2 = cipher.encrypt(text, 0x0000000000000000L); // Інший IV
        
        assertNotEquals(DES_OFB.toHex(enc1), DES_OFB.toHex(enc2), "Різні IV повинні створювати різний шифротекст для однакових повідомлень");
    }

    @Test
    public void testCoreDesBlockSymmetry() {
        // перевіряємо базовий алгоритм DES (1 блок = 64 біти)
        int[][] subkeys = DES.generateSubkeys(DEFAULT_KEY);
        long originalBlock = 0x1122334455667788L; // Довільний тестовий блок
        
        long encryptedBlock = DES.encrypt(originalBlock, subkeys);
        long decryptedBlock = DES.decrypt(encryptedBlock, subkeys);
        
        assertEquals(originalBlock, decryptedBlock, "Базовий клас DES має коректно шифрувати та розшифровувати 64-бітний блок");
        assertNotEquals(originalBlock, encryptedBlock, "Зашифрований блок не повинен дорівнювати відкритому");
    }

    @Test
    public void testEmptyInput() {
        // перевірка роботи з порожнім рядком
        DES_OFB cipher = new DES_OFB(DEFAULT_KEY);
        
        byte[] encrypted = cipher.encrypt("", DEFAULT_IV);
        assertEquals(0, encrypted.length, "Зашифрований порожній рядок має бути порожнім масивом байтів");
        
        String decrypted = cipher.decrypt(encrypted, DEFAULT_IV);
        assertEquals("", decrypted, "Розшифрований порожній масив має повертати порожній рядок");
    }
}
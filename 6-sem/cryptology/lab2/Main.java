import java.util.Scanner;

public class Main {

    public static void main(String[] args) {
        long key = 0x133457799BBCDFF1L;   // класичний тестовий ключ DES (64-бітні числа у форматі hex)
        long iv  = 0xABCDEF1234567890L;   // ініціалізаційний вектор iv (так само)

        DES_OFB cipher = new DES_OFB(key);

        System.out.println("  DES у режимі OFB");
        System.out.println("=".repeat(56));
        System.out.printf("  Ключ : %016x%n", key);
        System.out.printf("  IV   : %016x%n", iv);
        System.out.println();

        //тест 1: короткий рядок (менше 1 блоку = 8 байт)
        runTest(cipher, "Hello!", iv, "Тест 1 (< 1 блоку)");

        //тест 2: рядок довший за 1 блок
        runTest(cipher, "Today is sunny.", iv, "Тест 2 (> 1 блоку)");

        //тест 3: той самий текст з іншим iv
        System.out.println("  Тест 3 — вплив IV:");
        byte[] enc1 = cipher.encrypt("Hello!", iv);
        byte[] enc2 = cipher.encrypt("Hello!", 0x0000000000000000L);
        System.out.println("    IV оригінальний : " + DES_OFB.toHex(enc1));
        System.out.println("    IV = 0           : " + DES_OFB.toHex(enc2));
        System.out.println("    Різні результати : " +
            !DES_OFB.toHex(enc1).equals(DES_OFB.toHex(enc2)));
        System.out.println();

        //iнтерактивний режим
        System.out.println("=".repeat(56));
        System.out.print("  Текст для шифрування: ");
        Scanner scanner = new Scanner(System.in);
        String input = scanner.nextLine();
        byte[] encrypted = cipher.encrypt(input, iv);
        System.out.println("  Зашифровано : " + DES_OFB.toHex(encrypted));
        System.out.println("  Розшифровано: " + cipher.decrypt(encrypted, iv));
        scanner.close();
    }

    private static void runTest(DES_OFB cipher, String text, long iv, String label) {
        byte[] enc = cipher.encrypt(text, iv);
        String dec = cipher.decrypt(enc, iv);
        System.out.println("  " + label + ":");
        System.out.println("    Відкритий текст : " + text);
        System.out.println("    Зашифровано     : " + DES_OFB.toHex(enc));
        System.out.println("    Розшифровано    : " + dec);
        System.out.println("    OK              : " + text.equals(dec));
        System.out.println();
    }
}
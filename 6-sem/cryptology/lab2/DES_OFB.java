import java.nio.charset.StandardCharsets;


public class DES_OFB {

    private final int[][] subkeys;

    /**
     * @param key 64-бітний DES-ключ (реально 56 значущих біт)
     */
    public DES_OFB(long key) {
        this.subkeys = DES.generateSubkeys(key);
    }

    //генерація keystream і XOR із даними

    /**
     * шифрує або розшифровує байти у режимі OFB
     * симетрична операція process(process(data, iv), iv) == data.
     *
     * @param data   вхідні байти
     * @param ivLong ініціалізаційний вектор (64 біти)
     * @return результат
     */
    public byte[] process(byte[] data, long ivLong) {
        byte[] result = new byte[data.length];
        long O = ivLong;       // поточний блок keystream (починаємо з IV)
        int done = 0;

        while (done < data.length) {
            //O(i) — генеруємо наступний блок потоку
            O = DES.encrypt(O, subkeys);
            byte[] keystreamBlock = longToBytes(O);

            //XOR keystream із даними (до 8 байт за раз)
            int blockLen = Math.min(8, data.length - done);
            for (int i = 0; i < blockLen; i++)
                result[done + i] = (byte)(data[done + i] ^ keystreamBlock[i]);

            done += blockLen;
        }
        return result;
    }


    //обгортки для рядків

    /** шифрує рядок (UTF-8), повертає байти */
    public byte[] encrypt(String plaintext, long iv) {
        return process(plaintext.getBytes(StandardCharsets.UTF_8), iv);
    }

    /** розшифровує байти, повертає рядок */
    public String decrypt(byte[] ciphertext, long iv) {
        return new String(process(ciphertext, iv), StandardCharsets.UTF_8);
    }

    //допоміжні методи перетворення даних

    /** long -> 8 байт (big-endian) */
    private static byte[] longToBytes(long v) {
        byte[] b = new byte[8];
        for (int i = 7; i >= 0; i--) {
            b[i] = (byte)(v & 0xFF);
            v >>>= 8;
        }
        return b;
    }
    /** байти -> hex-рядок для виведення */
    public static String toHex(byte[] bytes) {
        StringBuilder sb = new StringBuilder();
        for (byte b : bytes)
            sb.append(String.format("%02x", b & 0xFF));
        return sb.toString();
    }
}
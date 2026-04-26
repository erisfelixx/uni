import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.charset.StandardCharsets;

public class MD4 {
    
    //початковий стан
    private static final int INIT_H1 = 0x67452301;
    private static final int INIT_H2 = 0xEFCDAB89;
    private static final int INIT_H3 = 0x98BADCFE;
    private static final int INIT_H4 = 0x10325476;

    private static final int K1 = 0x00000000; //раунд 1
    private static final int K2 = 0x5A827999; //раунд 2: floor(2^30 * sqrt(2))
    private static final int K3 = 0x6ED9EBA1; //раунд 3: floor(2^30 * sqrt(3))

    private static final int[] Z = {
        //порядок слів блоку для кожного раунду
        0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, //раунд 1
        0, 4, 8, 12, 1, 5, 9, 13, 2, 6, 10, 14, 3, 7, 11, 15, //раунд 2
        0, 8, 4, 12, 2, 10, 6, 14, 1, 9, 5, 13, 3, 11, 7, 15 //раунд 3
    };

    private static final int[] W = {
        //кількість бітів для циклічного зсуву на кожному кроці
        3, 7, 11, 19, 3, 7, 11, 19, 3, 7, 11, 19, 3, 7, 11, 19, //раунд 1
        3, 5, 9, 13, 3, 5, 9, 13, 3, 5, 9, 13, 3, 5, 9, 13, //раунд 2
        3, 9, 11, 15, 3, 9, 11, 15, 3, 9, 11, 15, 3, 9, 11, 15 //раунд 3
    };


    // -- побітові функції трьох раундів

    //раунд 1  - функція вибору: вибирає біти з c або d залежно від b
    private static int f(int b, int c, int d) {
        return (b & c) | (~b & d);
    }

    //раунд 2 - функція більшості
    private static int g(int b, int c, int d) {
        return (b & c) | (b & d) | (c & d);
    }

    //раунд 3 - функція парності - змішує біти через xor
    private static int h(int b, int c, int d) {
        return b ^ c ^ d;
    }

    //циклічний зсув вліво на s позицій для 32-бітного числа
    private static int leftRotate(int value, int s) {
        return (value << s) | (value >>> (32 - s));
    }


    //padding - доповнення повідомлення до 512 бітів: 
    // 1) байт 0x80
    // 2) нулі до 56 байт mod 64
    // 3) +довжина оригінального повідомлення у бітах (8 байт, little-endian)
    private static byte[] pad(byte[] message) {
        int originalLen = message.length;
        long bitLen = (long) originalLen * 8;
 
        int padLen = (originalLen % 64 < 56)
            ? 56 - (originalLen % 64)
            : 120 - (originalLen % 64);
 
        byte[] padded = new byte[originalLen + padLen + 8];
        System.arraycopy(message, 0, padded, 0, originalLen);
 
        padded[originalLen] = (byte) 0x80;
 
        ByteBuffer.wrap(padded, originalLen + padLen, 8)
                  .order(ByteOrder.LITTLE_ENDIAN)
                  .putLong(bitLen);
 
        return padded;
    }


    //основна функція обчислення MD4
    /**
     * @param message вхідні дані
     * @return 16-байтний масив (хеш)
     */
    
    public static byte[] hash(byte[] message) {
        int H1 = INIT_H1;
        int H2 = INIT_H2;
        int H3 = INIT_H3;
        int H4 = INIT_H4;
 
        byte[] padded = pad(message);
        ByteBuffer buf = ByteBuffer.wrap(padded).order(ByteOrder.LITTLE_ENDIAN);
 
        while (buf.hasRemaining()) {
            int[] X = new int[16];
            for (int i = 0; i < 16; i++) {
                X[i] = buf.getInt();
            }
 
            int A = H1, B = H2, C = H3, D = H4;
 
            for (int j = 0; j < 48; j++) {
                int funcResult;
                int k;
 
                if (j < 16) {
                    funcResult = f(B, C, D);
                    k = K1;
                } else if (j < 32) {
                    funcResult = g(B, C, D);
                    k = K2;
                } else {
                    funcResult = h(B, C, D);
                    k = K3;
                }
 
                int t = leftRotate(A + funcResult + X[Z[j]] + k, W[j]);
 
                A = D;
                D = C;
                C = B;
                B = t;
            }
            H1 += A;
            H2 += B;
            H3 += C;
            H4 += D;
        }
 
        return ByteBuffer.allocate(16)
                         .order(ByteOrder.LITTLE_ENDIAN)
                         .putInt(H1).putInt(H2)
                         .putInt(H3).putInt(H4)
                         .array();
    }

    /**
     *обгортка: рядок -> hex-рядок хешу
     *
     * @param text вхідний рядок (UTF-8)
     * @return хеш у вигляді рядка з 32 hex-символів
     */
    public static String hashHex(String text) {
        byte[] digest = hash(text.getBytes(StandardCharsets.UTF_8));
        StringBuilder sb = new StringBuilder(32);
        for (byte b : digest) {
            sb.append(String.format("%02x", b & 0xFF));
        }
        return sb.toString();
    }


}
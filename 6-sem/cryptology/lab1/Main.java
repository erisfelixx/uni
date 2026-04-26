import java.util.Scanner;

public class Main {
    public static void main(String[] args) {
        Scanner scanner = new Scanner(System.in);

        System.out.println("\nMD4 hash generator");
        System.out.print("Enter text for hashing: ");
        String text = scanner.nextLine();

        System.out.println("Hash: " + MD4.hashHex(text));

        scanner.close();
    }
}
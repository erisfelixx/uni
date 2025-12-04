package org.example;

import org.example.model.*;
import org.example.service.TrainManager;
import org.example.utils.FileManager;

import java.util.List;
import java.util.Scanner;

public class Main {
    public static void main(String[] args) {
        TrainManager train = new TrainManager();
        FileManager fileManager = new FileManager();
        Scanner scanner = new Scanner(System.in);

        // Додамо трохи вагонів для старту (щоб не було пусто)
        seedTrain(train);

        while (true) {
            System.out.println("\n=== СИСТЕМА УПРАВЛІННЯ ПОЇЗДОМ ===");
            System.out.println("1. Показати склад поїзда");
            System.out.println("2. Порахувати загальну кількість пасажирів");
            System.out.println("3. Порахувати загальну вагу багажу");
            System.out.println("4. Посортувати вагони за комфортом");
            System.out.println("5. Знайти вагони за діапазоном пасажирів");
            System.out.println("6. Зберегти поїзд у файл (JSON)");
            System.out.println("7. Завантажити поїзд з файлу");
            System.out.println("8. ДОДАТИ ВАГОН ВРУЧНУ"); // <--- Новий пункт
            System.out.println("0. Вихід");
            System.out.print("Ваш вибір: ");

            String choice = scanner.nextLine();

            switch (choice) {
                case "1":
                    printTrain(train.getWagons());
                    break;
                case "2":
                    System.out.println("Загальна кількість пасажирів: " + train.getTotalPassengers());
                    break;
                case "3":
                    System.out.println("Загальна вага багажу: " + train.getTotalLuggage() + " кг");
                    break;
                case "4":
                    train.sortByComfort();
                    System.out.println("Вагони відсортовано! Натисніть 1, щоб переглянути.");
                    break;
                case "5":
                    findWagons(train, scanner);
                    break;
                case "6":
                    fileManager.saveToFile(train.getWagons());
                    break;
                case "7":
                    List<RollingStock> loadedWagons = fileManager.readTrain();
                    train = new TrainManager();
                    for (RollingStock w : loadedWagons) train.addWagon(w);
                    System.out.println("Поїзд оновлено з файлу!");
                    break;
                case "8":
                    addNewWagon(train, scanner); // <--- Виклик нового методу
                    break;
                case "0":
                    System.out.println("До побачення!");
                    return;
                default:
                    System.out.println("Невірний вибір. Спробуйте ще раз.");
            }
        }
    }

    // Метод для додавання вагона через консоль
    private static void addNewWagon(TrainManager train, Scanner scanner) {
        System.out.println("\n--- Додавання нового вагона ---");
        System.out.println("Оберіть тип вагона:");
        System.out.println("1. Люкс (High comfort, макс 18 місць)");
        System.out.println("2. Купе (Medium comfort, макс 36 місць)");
        System.out.println("3. Плацкарт (Low comfort, макс 54 місця)");
        System.out.print("Ваш вибір: ");

        String type = scanner.nextLine();

        try {
            System.out.print("Введіть ID вагона (номер): ");
            int id = Integer.parseInt(scanner.nextLine());

            System.out.print("Введіть кількість пасажирів: ");
            int passengers = Integer.parseInt(scanner.nextLine());

            System.out.print("Введіть вагу багажу (кг): ");
            int luggage = Integer.parseInt(scanner.nextLine());

            switch (type) {
                case "1":
                    train.addWagon(new LuxuryCarriage(id, passengers, luggage));
                    System.out.println("Вагон ЛЮКС додано!");
                    break;
                case "2":
                    train.addWagon(new CoupeCarriage(id, passengers, luggage));
                    System.out.println("Вагон КУПЕ додано!");
                    break;
                case "3":
                    train.addWagon(new PlaczkartCarriage(id, passengers, luggage));
                    System.out.println("Вагон ПЛАЦКАРТ додано!");
                    break;
                default:
                    System.out.println("Невірний тип вагона!");
            }
        } catch (NumberFormatException e) {
            System.out.println("Помилка: Вводьте лише цифри!");
        }
    }

    private static void findWagons(TrainManager train, Scanner scanner) {
        System.out.print("Введіть мінімум пасажирів: ");
        int min = Integer.parseInt(scanner.nextLine());
        System.out.print("Введіть максимум пасажирів: ");
        int max = Integer.parseInt(scanner.nextLine());
        List<RollingStock> found = train.findCarriagesByPassengerRange(min, max);
        System.out.println("Знайдено вагонів: " + found.size());
        printTrain(found);
    }

    private static void seedTrain(TrainManager train) {
        train.addWagon(new LuxuryCarriage(101, 10, 200));
        train.addWagon(new CoupeCarriage(201, 36, 500));
        train.addWagon(new PlaczkartCarriage(301, 50, 800));
        train.addWagon(new CoupeCarriage(202, 15, 100));
    }

    private static void printTrain(List<RollingStock> wagons) {
        if (wagons.isEmpty()) {
            System.out.println("Список порожній.");
        } else {
            for (RollingStock w : wagons) {
                System.out.println(w);
            }
        }
    }
}
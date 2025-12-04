package org.example.utils;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import com.google.gson.reflect.TypeToken;
import org.example.model.*;

import java.io.*;
import java.lang.reflect.Type;
import java.util.ArrayList;
import java.util.List;

public class FileManager {
    private static final String FILE_NAME = "train.json";
    private final Gson gson;

    public FileManager() {
        RuntimeTypeAdapterFactory<RollingStock> adapter = RuntimeTypeAdapterFactory.of(RollingStock.class, "type")
                .registerSubtype(LuxuryCarriage.class, "Luxury")
                .registerSubtype(CoupeCarriage.class, "Coupe")
                .registerSubtype(PlaczkartCarriage.class, "Placzkart");

        this.gson = new GsonBuilder()
                .registerTypeAdapterFactory(adapter) // підключаємо адаптер
                .setPrettyPrinting()
                .create();
    }

    // збереження списку вагонів у JSON файл
    public void saveToFile(List<RollingStock> wagons) {
        try (FileWriter writer = new FileWriter(FILE_NAME)) {
            gson.toJson(wagons, writer);
            System.out.println("Дані успішно збережено у файл " + FILE_NAME);
        } catch (IOException e) {
            System.err.println("Помилка запису у файл: " + e.getMessage());
        }
    }

    public List<RollingStock> readTrain() {
        try (FileReader reader = new FileReader(FILE_NAME)) {

            Type listType = new TypeToken<List<RollingStock>>(){}.getType();
            List<RollingStock> wagons = gson.fromJson(reader, listType);

            if (wagons == null) {
                return new ArrayList<>();
            }

            System.out.println("Поїзд успішно зчитано з файлу! Кількість вагонів: " + wagons.size());
            return wagons;
        } catch (FileNotFoundException e) {
            System.out.println("Файл збереження не знайдено. Створено новий порожній поїзд.");
            return new ArrayList<>();
        } catch (IOException e) {
            System.err.println("Помилка зчитування файлу: " + e.getMessage());
            return new ArrayList<>();
        }
    }
}
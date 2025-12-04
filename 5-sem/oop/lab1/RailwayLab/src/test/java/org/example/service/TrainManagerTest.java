package org.example.service;

import org.example.model.*;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import java.util.List;

import static org.junit.jupiter.api.Assertions.*;

/**
 * Клас для тестування бізнес-логіки TrainManager.
 * Використовує JUnit 5.
 */
class TrainManagerTest {

    private TrainManager trainManager;

    @BeforeEach
    void setUp() {
        // Цей метод запускається перед КОЖНИМ тестом.
        // Ми створюємо чистий менеджер і наповнюємо його даними.
        trainManager = new TrainManager();
        trainManager.addWagon(new LuxuryCarriage(1, 10, 100)); // Люкс (High comfort)
        trainManager.addWagon(new PlaczkartCarriage(2, 50, 500)); // Плацкарт (Low comfort)
        trainManager.addWagon(new CoupeCarriage(3, 20, 200));  // Купе (Medium comfort)
    }

    @Test
    void testGetTotalPassengers() {
        // 10 + 50 + 20 = 80
        assertEquals(80, trainManager.getTotalPassengers(), "Загальна кількість пасажирів має бути 80");
    }

    @Test
    void testGetTotalLuggage() {
        // 100 + 500 + 200 = 800
        assertEquals(800, trainManager.getTotalLuggage(), "Загальна вага багажу має бути 800");
    }

    @Test
    void testSortByComfort() {
        // До сортування порядок: High, Low, Medium
        trainManager.sortByComfort();

        List<RollingStock> wagons = trainManager.getWagons();

        // Після сортування має бути: High, Medium, Low
        assertEquals(ComfortLevel.HIGH, ((PassengerCarriage) wagons.get(0)).getComfortLevel());
        assertEquals(ComfortLevel.MEDIUM, ((PassengerCarriage) wagons.get(1)).getComfortLevel());
        assertEquals(ComfortLevel.LOW, ((PassengerCarriage) wagons.get(2)).getComfortLevel());
    }

    @Test
    void testFindCarriagesByPassengerRange() {
        // Шукаємо вагони, де від 15 до 30 пасажирів.
        // Має знайтися тільки Купе (20 пасажирів).
        List<RollingStock> found = trainManager.findCarriagesByPassengerRange(15, 30);

        assertEquals(1, found.size());
        assertEquals(20, ((PassengerCarriage) found.get(0)).getPassengerCount());
    }

    @Test
    void testFindCarriagesByPassengerRange_NotFound() {
        // Шукаємо нереальний діапазон
        List<RollingStock> found = trainManager.findCarriagesByPassengerRange(1000, 2000);
        assertTrue(found.isEmpty());
    }
}
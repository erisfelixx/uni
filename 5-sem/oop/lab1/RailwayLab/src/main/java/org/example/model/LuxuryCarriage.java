package org.example.model;

public class LuxuryCarriage extends PassengerCarriage {
    private static final int MAX_PASSENGERS = 18;

    public LuxuryCarriage(int id, int passengerCount, int luggageCount) {
        super(id, 58.0, 24.5, passengerCount, luggageCount, ComfortLevel.HIGH);
        if (passengerCount > MAX_PASSENGERS) {
            System.err.println("Помилка: У вагоні Люкс не може бути більше " + MAX_PASSENGERS + " пасажирів!");
        }
    }

    @Override
    public String toString() {
        return "Вагон [ЛЮКС] -> " + super.toString();
    }
}
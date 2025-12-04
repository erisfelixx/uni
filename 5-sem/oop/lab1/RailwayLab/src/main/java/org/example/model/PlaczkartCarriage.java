package org.example.model;

public class PlaczkartCarriage extends PassengerCarriage {
    private static final int MAX_PASSENGERS = 54;

    public PlaczkartCarriage(int id, int passengerCount, int luggageCount) {
        super(id, 52.0, 24.5, passengerCount, luggageCount, ComfortLevel.LOW);
        if (passengerCount > MAX_PASSENGERS) {
            System.err.println("Помилка: У Плацкарті не може бути більше " + MAX_PASSENGERS + " пасажирів!");
        }
    }

    @Override
    public String toString() {
        return "Вагон [ПЛАЦКАРТ] -> " + super.toString();
    }
}
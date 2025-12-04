package org.example.model;

public class CoupeCarriage extends PassengerCarriage {
    private static final int MAX_PASSENGERS = 36;

    public CoupeCarriage(int id, int passengerCount, int luggageCount) {
        super(id, 54.0, 24.5, passengerCount, luggageCount, ComfortLevel.MEDIUM);
        if (passengerCount > MAX_PASSENGERS) {
            System.err.println("Помилка: У вагоні Купе не може бути більше " + MAX_PASSENGERS + " пасажирів!");
        }
    }

    @Override
    public String toString() {
        return "Вагон [КУПЕ] -> " + super.toString();
    }
}
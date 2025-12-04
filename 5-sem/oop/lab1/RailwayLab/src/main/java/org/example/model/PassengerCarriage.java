package org.example.model;

public abstract class PassengerCarriage extends RollingStock {
    private int passengerCount;
    private int luggageCount;
    private ComfortLevel comfortLevel;

    public PassengerCarriage(int id, double mass, double length, int passengerCount, int luggageCount, ComfortLevel comfortLevel) {
        super(id, mass, length);
        this.passengerCount = passengerCount;
        this.luggageCount = luggageCount;
        this.comfortLevel = comfortLevel;
    }

    public int getPassengerCount() { return passengerCount; }
    public int getLuggageCount() { return luggageCount; }
    public ComfortLevel getComfortLevel() { return comfortLevel; }

    @Override
    public String toString() {
        return super.toString() + ", Пасажирів: " + passengerCount + ", Багаж: " + luggageCount + ", Комфорт: " + comfortLevel;
    }
}
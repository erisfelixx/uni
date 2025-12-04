package org.example.model;

public abstract class RollingStock {
    private int id;
    private double mass;
    private double length;

    public RollingStock(int id, double mass, double length) {
        this.id = id;
        this.mass = mass;
        this.length = length;
    }

    public int getId() { return id; }
    public double getMass() { return mass; }
    public double getLength() { return length; }

    @Override
    public String toString() {
        return "ID: " + id + ", Маса: " + mass + "т, Довжина: " + length + "м";
    }
}
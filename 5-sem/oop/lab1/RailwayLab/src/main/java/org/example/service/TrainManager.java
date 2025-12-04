package org.example.service;

import org.example.model.PassengerCarriage;
import org.example.model.RollingStock;
import org.example.model.ComfortLevel;

import java.util.ArrayList;
import java.util.List;
import java.util.stream.Collectors;

public class TrainManager {
    private List<RollingStock> wagons;

    public TrainManager() {
        this.wagons = new ArrayList<>();
    }

    public void addWagon(RollingStock wagon) {
        wagons.add(wagon);
    }

    public List<RollingStock> getWagons() {
        return wagons;
    }

    public int getTotalPassengers() {
        int total = 0;
        for (RollingStock wagon : wagons) {
            if (wagon instanceof PassengerCarriage) {
                total += ((PassengerCarriage) wagon).getPassengerCount();
            }
        }
        return total;
    }

    public int getTotalLuggage() {
        return wagons.stream()
                .filter(w -> w instanceof PassengerCarriage)
                .mapToInt(w -> ((PassengerCarriage) w).getLuggageCount())
                .sum();
    }

    public void sortByComfort() {
        wagons.sort((w1, w2) -> {
            if (w1 instanceof PassengerCarriage && w2 instanceof PassengerCarriage) {
                ComfortLevel c1 = ((PassengerCarriage) w1).getComfortLevel();
                ComfortLevel c2 = ((PassengerCarriage) w2).getComfortLevel();
                return c1.compareTo(c2);
            }
            return 0;
        });
    }

    public List<RollingStock> findCarriagesByPassengerRange(int min, int max) {
        return wagons.stream()
                .filter(w -> w instanceof PassengerCarriage)
                .map(w -> (PassengerCarriage) w)
                .filter(pc -> pc.getPassengerCount() >= min && pc.getPassengerCount() <= max)
                .collect(Collectors.toList());
    }
}
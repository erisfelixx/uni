package ua.oop.travel.travelagency.service;

import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import ua.oop.travel.travelagency.entity.Tour;
import ua.oop.travel.travelagency.repository.TourRepository;

import java.util.List;

@Service
@RequiredArgsConstructor
public class TourService {

    private final TourRepository tourRepository;

    public List<Tour> getAllTours() {
        return tourRepository.findAll();
    }

    public List<Tour> getHotTours() {
        return tourRepository.findByIsHotTrue();
    }

    public Tour setHotStatus(Integer tourId, boolean isHot) {
        Tour tour = tourRepository.findById(tourId)
                .orElseThrow(() -> new RuntimeException("Tour not found"));
        tour.setIsHot(isHot);
        return tourRepository.save(tour);
    }
}
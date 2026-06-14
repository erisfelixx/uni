package ua.oop.travel.travelagency.controller;

import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import ua.oop.travel.travelagency.entity.Tour;
import ua.oop.travel.travelagency.service.TourService;

import java.util.List;

@RestController
@RequestMapping("/api/tours")
@CrossOrigin
@RequiredArgsConstructor
public class TourController {

    private final TourService tourService;

    @GetMapping
    public List<Tour> getAllTours() {
        return tourService.getAllTours();
    }

    @GetMapping("/hot")
    public List<Tour> getHotTours() {
        return tourService.getHotTours();
    }

    @PatchMapping("/{id}/hot")
    public ResponseEntity<Tour> setHotStatus(@PathVariable Integer id, @RequestParam boolean isHot) {
        return ResponseEntity.ok(tourService.setHotStatus(id, isHot));
    }
}
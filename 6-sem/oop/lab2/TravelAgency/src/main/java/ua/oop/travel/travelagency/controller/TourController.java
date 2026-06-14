package ua.oop.travel.travelagency.controller;

import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import ua.oop.travel.travelagency.dto.TourDto;
import ua.oop.travel.travelagency.mapper.TourMapper;
import ua.oop.travel.travelagency.service.TourService;

import java.util.List;

@RestController
@RequestMapping("/api/tours")
@CrossOrigin
@RequiredArgsConstructor
public class TourController {

    private final TourService tourService;
    private final TourMapper tourMapper;

    @GetMapping
    public List<TourDto> getAllTours() {
        return tourMapper.toDtoList(tourService.getAllTours());
    }

    @GetMapping("/hot")
    public List<TourDto> getHotTours() {
        return tourMapper.toDtoList(tourService.getHotTours());
    }

    @PatchMapping("/{id}/hot")
    public ResponseEntity<TourDto> setHotStatus(@PathVariable Integer id, @RequestParam boolean isHot) {
        return ResponseEntity.ok(tourMapper.toDto(tourService.setHotStatus(id, isHot)));
    }
}
package ua.oop.travel.travelagency.service;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import ua.oop.travel.travelagency.entity.Tour;
import ua.oop.travel.travelagency.repository.TourRepository;

import java.math.BigDecimal;
import java.util.List;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.mockito.Mockito.when;

@ExtendWith(MockitoExtension.class)
public class TourServiceTest {

    @Mock
    private TourRepository tourRepository;

    @InjectMocks
    private TourService tourService;

    @Test
    public void testGetHotTours() {
        // Дано (Given)
        Tour hotTour = new Tour();
        hotTour.setId(1);
        hotTour.setTitle("Hot Turkey");
        hotTour.setIsHot(true);
        hotTour.setBasePrice(new BigDecimal("500.00"));

        when(tourRepository.findByIsHotTrue()).thenReturn(List.of(hotTour));

        List<Tour> result = tourService.getHotTours();

        assertEquals(1, result.size());
        assertEquals("Hot Turkey", result.get(0).getTitle());
    }
}
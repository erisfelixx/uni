package ua.oop.travel.travelagency.service;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import ua.oop.travel.travelagency.entity.Booking;
import ua.oop.travel.travelagency.entity.Discount;
import ua.oop.travel.travelagency.entity.Tour;
import ua.oop.travel.travelagency.entity.User;
import ua.oop.travel.travelagency.repository.BookingRepository;
import ua.oop.travel.travelagency.repository.DiscountRepository;
import ua.oop.travel.travelagency.repository.TourRepository;
import ua.oop.travel.travelagency.repository.UserRepository;

import java.math.BigDecimal;
import java.util.Optional;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
public class BookingServiceTest {

    @Mock private BookingRepository bookingRepository;
    @Mock private TourRepository tourRepository;
    @Mock private UserRepository userRepository;
    @Mock private DiscountRepository discountRepository;

    @InjectMocks private BookingService bookingService;

    @Test
    public void createBooking_NoDiscountForNewCustomer() {
        // Arrange
        User user = new User();
        user.setId(1);

        Tour tour = new Tour();
        tour.setId(101);
        tour.setBasePrice(new BigDecimal("1000.00"));

        when(userRepository.findById(1)).thenReturn(Optional.of(user));
        when(tourRepository.findById(101)).thenReturn(Optional.of(tour));
        when(discountRepository.findByUserId(1)).thenReturn(Optional.empty()); // No discount

        when(bookingRepository.save(any(Booking.class))).thenAnswer(i -> i.getArgument(0));

        Booking result = bookingService.createBooking(1, 101);

        assertEquals(new BigDecimal("1000.00"), result.getFinalPrice());
        verify(bookingRepository, times(1)).save(any(Booking.class));
    }

    @Test
    public void createBooking_AppliesDiscount() {
        // Arrange
        User user = new User();
        user.setId(99);

        Tour tour = new Tour();
        tour.setId(102);
        tour.setBasePrice(new BigDecimal("1000.00"));

        Discount discount = new Discount();
        discount.setDiscountPercentage(new BigDecimal("10.00")); // 10% discount

        when(userRepository.findById(99)).thenReturn(Optional.of(user));
        when(tourRepository.findById(102)).thenReturn(Optional.of(tour));
        when(discountRepository.findByUserId(99)).thenReturn(Optional.of(discount));

        when(bookingRepository.save(any(Booking.class))).thenAnswer(i -> i.getArgument(0));

        Booking result = bookingService.createBooking(99, 102);

        assertEquals(0, new BigDecimal("900.00").compareTo(result.getFinalPrice()));
        verify(bookingRepository, times(1)).save(any(Booking.class));
    }
}
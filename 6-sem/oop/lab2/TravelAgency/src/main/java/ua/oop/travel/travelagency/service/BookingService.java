package ua.oop.travel.travelagency.service;

import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import ua.oop.travel.travelagency.entity.*;
import ua.oop.travel.travelagency.repository.*;

import java.math.BigDecimal;

@Service
@RequiredArgsConstructor
public class BookingService {

    private final BookingRepository bookingRepository;
    private final TourRepository tourRepository;
    private final UserRepository userRepository;
    private final DiscountRepository discountRepository;
    private final PaymentRepository paymentRepository;

    @Transactional
    public Booking createBooking(Integer customerId, Integer tourId) {
        User customer = userRepository.findById(customerId)
                .orElseThrow(() -> new RuntimeException("Customer not found"));
        Tour tour = tourRepository.findById(tourId)
                .orElseThrow(() -> new RuntimeException("Tour not found"));

        BigDecimal finalPrice = tour.getBasePrice();

        Discount discount = discountRepository.findByUserId(customerId).orElse(null);
        if (discount != null) {
            BigDecimal discountMultiplier = BigDecimal.ONE.subtract(
                    discount.getDiscountPercentage().divide(BigDecimal.valueOf(100))
            );
            finalPrice = finalPrice.multiply(discountMultiplier);
        }

        Booking booking = Booking.builder()
                .customer(customer)
                .tour(tour)
                .status("PENDING")
                .finalPrice(finalPrice)
                .build();

        return bookingRepository.save(booking);
    }

    @Transactional
    public Payment payForBooking(Integer bookingId) {
        Booking booking = bookingRepository.findById(bookingId)
                .orElseThrow(() -> new RuntimeException("Booking not found"));

        if ("PAID".equals(booking.getStatus())) {
            throw new RuntimeException("Booking is already paid");
        }

        booking.setStatus("PAID");
        bookingRepository.save(booking);

        Payment payment = Payment.builder()
                .booking(booking)
                .amount(booking.getFinalPrice())
                .build();

        return paymentRepository.save(payment);
    }
}
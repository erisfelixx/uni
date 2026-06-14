package ua.oop.travel.travelagency.controller;

import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import ua.oop.travel.travelagency.entity.Booking;
import ua.oop.travel.travelagency.entity.Payment;
import ua.oop.travel.travelagency.service.BookingService;

@RestController
@RequestMapping("/api/bookings")
@CrossOrigin
@RequiredArgsConstructor
public class BookingController {

    private final BookingService bookingService;

    @PostMapping
    public ResponseEntity<Booking> createBooking(@RequestParam Integer customerId, @RequestParam Integer tourId) {
        return ResponseEntity.ok(bookingService.createBooking(customerId, tourId));
    }

    @PostMapping("/{id}/pay")
    public ResponseEntity<Payment> payForBooking(@PathVariable Integer id) {
        return ResponseEntity.ok(bookingService.payForBooking(id));
    }
}
package ua.oop.travel.travelagency.controller;

import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import ua.oop.travel.travelagency.dto.BookingDto;
import ua.oop.travel.travelagency.entity.Payment;
import ua.oop.travel.travelagency.mapper.BookingMapper;
import ua.oop.travel.travelagency.service.BookingService;

@RestController
@RequestMapping("/api/bookings")
@CrossOrigin
@RequiredArgsConstructor
public class BookingController {

    private final BookingService bookingService;
    private final BookingMapper bookingMapper;

    @PostMapping
    public ResponseEntity<BookingDto> createBooking(@RequestParam Integer customerId, @RequestParam Integer tourId) {
        return ResponseEntity.ok(bookingMapper.toDto(bookingService.createBooking(customerId, tourId)));
    }

    @PostMapping("/{id}/pay")
    public ResponseEntity<Payment> payForBooking(@PathVariable Integer id) {
        // Залишаємо Payment як є, оскільки DTO для нього поки немає
        return ResponseEntity.ok(bookingService.payForBooking(id));
    }
}
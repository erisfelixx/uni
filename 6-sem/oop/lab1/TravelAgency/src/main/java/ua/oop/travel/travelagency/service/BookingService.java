package ua.oop.travel.travelagency.service;

import ua.oop.travel.travelagency.dao.BookingDao;
import ua.oop.travel.travelagency.dto.BookingDto;
import ua.oop.travel.travelagency.mapper.BookingMapper;
import ua.oop.travel.travelagency.model.Booking;

import java.sql.SQLException;
import java.time.LocalDateTime;
import java.util.List;

public class BookingService {
    private final BookingDao bookingDao = new BookingDao();
    private final BookingMapper bookingMapper = BookingMapper.INSTANCE;

    // створення нового бронювання
    public BookingDto createBooking(BookingDto bookingDto) throws SQLException {
        Booking booking = bookingMapper.toModel(bookingDto);

        // бізнес-логіка: автоматично встановлюємо дату та статус, якщо вони порожні
        if (booking.getCreatedAt() == null) {
            booking.setCreatedAt(LocalDateTime.now());
        }
        if (booking.getStatus() == null || booking.getStatus().isEmpty()) {
            booking.setStatus("PENDING");
        }

        Booking savedBooking = bookingDao.save(booking);
        return bookingMapper.toDto(savedBooking);
    }

    // отримання всіх бронювань конкретного клієнта
    public List<BookingDto> getBookingsByCustomer(Integer customerId) throws SQLException {
        List<Booking> bookings = bookingDao.findAllByCustomerId(customerId);
        return bookingMapper.toDtoList(bookings);
    }
}
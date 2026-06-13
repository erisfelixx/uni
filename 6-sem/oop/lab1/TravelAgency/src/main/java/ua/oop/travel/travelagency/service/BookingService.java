package ua.oop.travel.travelagency.service;

import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;
import ua.oop.travel.travelagency.dao.BookingDao;
import ua.oop.travel.travelagency.dto.BookingDto;
import ua.oop.travel.travelagency.mapper.BookingMapper;
import ua.oop.travel.travelagency.model.Booking;

import java.math.BigDecimal;
import java.sql.SQLException;
import java.time.LocalDateTime;
import java.util.List;

public class BookingService {
    private static final Logger logger = LogManager.getLogger(BookingService.class);
    private BookingDao bookingDao = new BookingDao();
    private final BookingMapper bookingMapper = BookingMapper.INSTANCE;

    // створення нового бронювання зі знижками
    public BookingDto createBooking(BookingDto bookingDto) throws SQLException {
        Booking booking = bookingMapper.toModel(bookingDto);

        // бізнес-логіка: автоматично встановлюємо дату та статус, якщо вони порожні
        if (booking.getCreatedAt() == null) {
            booking.setCreatedAt(LocalDateTime.now());
        }
        if (booking.getStatus() == null || booking.getStatus().isEmpty()) {
            booking.setStatus("PENDING");
        }

        // перевірка лояльності: якщо у клієнта вже є 2 або більше бронювань, він отримує 10% знижки на це (3-тє і далі)
        List<Booking> existingBookings = bookingDao.findAllByCustomerId(booking.getCustomerId());
        if (existingBookings.size() >= 2) {
            BigDecimal originalPrice = booking.getFinalPrice();
            // рахуємо 90% від початкової ціни (знижка 10%)
            BigDecimal discountedPrice = originalPrice.multiply(new BigDecimal("0.90"));
            booking.setFinalPrice(discountedPrice);

            logger.info("Застосовано знижку 10% для лояльного клієнта з ID {}. стара ціна: {}, нова ціна: {}",
                    booking.getCustomerId(), originalPrice, discountedPrice);
        }

        Booking savedBooking = bookingDao.save(booking);
        logger.info("Успішно створено бронювання з ID {} для клієнта з ID {}", savedBooking.getId(), savedBooking.getCustomerId());

        return bookingMapper.toDto(savedBooking);
    }

    // отримання всіх бронювань конкретного клієнта
    public List<BookingDto> getBookingsByCustomer(Integer customerId) throws SQLException {
        logger.info("Отримання списку бронювань для клієнта з ID {}", customerId);
        List<Booking> bookings = bookingDao.findAllByCustomerId(customerId);
        return bookingMapper.toDtoList(bookings);
    }
}
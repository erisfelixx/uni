package ua.oop.travel.travelagency.service;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import ua.oop.travel.travelagency.dao.BookingDao;
import ua.oop.travel.travelagency.dto.BookingDto;
import ua.oop.travel.travelagency.model.Booking;

import java.math.BigDecimal;
import java.sql.SQLException;
import java.util.List;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

// підключаємо Mockito до нашого тестового класу
@ExtendWith(MockitoExtension.class)
class BookingServiceTest {

    // створюємо "фейковий" DAO, який не ходить у базу даних
    @Mock
    private BookingDao bookingDao;

    // просимо Mockito підставити наш фейковий DAO всередину реального BookingService
    @InjectMocks
    private BookingService bookingService;

    @Test
    void createBooking_NoDiscountForNewCustomer() throws SQLException {
        // 1. ПІДГОТОВКА ДАНИХ (Arrange)
        BookingDto requestDto = new BookingDto();
        requestDto.setCustomerId(1);
        requestDto.setTourId(101); // ДОДАНО: обов'язкове поле для уникнення NullPointerException
        requestDto.setFinalPrice(new BigDecimal("1000.00"));

        // вчимо фейковий DAO відповідати: "у цього клієнта ще 0 бронювань"
        when(bookingDao.findAllByCustomerId(1)).thenReturn(List.of());

        // вчимо фейковий DAO при збереженні просто повертати те, що йому передали
        when(bookingDao.save(any(Booking.class))).thenAnswer(invocation -> invocation.getArgument(0));

        // 2. ВИКОНАННЯ (Act)
        BookingDto resultDto = bookingService.createBooking(requestDto);

        // 3. ПЕРЕВІРКА (Assert)
        // очікуємо, що ціна залишиться 1000.00
        assertEquals(new BigDecimal("1000.00"), resultDto.getFinalPrice());

        // перевіряємо, що сервіс рівно 1 раз викликав метод пошуку і 1 раз метод збереження
        verify(bookingDao, times(1)).findAllByCustomerId(1);
        verify(bookingDao, times(1)).save(any(Booking.class));
    }

    @Test
    void createBooking_AppliesDiscountForLoyalCustomer() throws SQLException {
        // 1. ПІДГОТОВКА ДАНИХ (Arrange)
        BookingDto requestDto = new BookingDto();
        requestDto.setCustomerId(99);
        requestDto.setTourId(102); // ДОДАНО: обов'язкове поле для уникнення NullPointerException
        requestDto.setFinalPrice(new BigDecimal("1000.00")); // початкова ціна 1000

        // створюємо два фейкові попередні бронювання
        Booking pastBooking1 = new Booking();
        Booking pastBooking2 = new Booking();

        // вчимо фейковий DAO відповідати: "у цього клієнта вже є 2 бронювання"
        when(bookingDao.findAllByCustomerId(99)).thenReturn(List.of(pastBooking1, pastBooking2));

        // вчимо фейковий DAO повертати переданий об'єкт
        when(bookingDao.save(any(Booking.class))).thenAnswer(invocation -> invocation.getArgument(0));

        // 2. ВИКОНАННЯ (Act)
        BookingDto resultDto = bookingService.createBooking(requestDto);

        // 3. ПЕРЕВІРКА (Assert)
        // очікуємо, що ціна стала 900.00 (1000 мінус 10%)
        // використовуємо compareTo для порівняння BigDecimal, бо "900.00" і "900.0" математично рівні
        assertEquals(0, new BigDecimal("900.00").compareTo(resultDto.getFinalPrice()),
                "Ціна має бути знижена на 10%");
    }
}
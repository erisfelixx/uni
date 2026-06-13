package ua.oop.travel.travelagency.servlet;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.datatype.jsr310.JavaTimeModule;
import jakarta.servlet.annotation.WebServlet;
import jakarta.servlet.http.HttpServlet;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import ua.oop.travel.travelagency.dto.BookingDto;
import ua.oop.travel.travelagency.service.BookingService;

import java.io.IOException;
import java.util.List;
import java.util.Map;

@WebServlet("/api/bookings")
public class BookingServlet extends HttpServlet {

    private final BookingService bookingService = new BookingService();
    private final ObjectMapper objectMapper = new ObjectMapper();

    @Override
    public void init() {
        // навчаємо  парсер працювати з LocalDateTime
        objectMapper.registerModule(new JavaTimeModule());
        objectMapper.disable(com.fasterxml.jackson.databind.SerializationFeature.WRITE_DATES_AS_TIMESTAMPS);
    }

    // отримання бронювань конкретного користувача (наприклад: /api/bookings?customerId=1)
    @Override
    protected void doGet(HttpServletRequest request, HttpServletResponse response) throws IOException {
        response.setContentType("application/json");
        response.setCharacterEncoding("UTF-8");

        try {
            String customerIdParam = request.getParameter("customerId");

            if (customerIdParam == null || customerIdParam.isEmpty()) {
                response.setStatus(HttpServletResponse.SC_BAD_REQUEST);
                objectMapper.writeValue(response.getWriter(), Map.of("error", "Необхідно вказати параметр customerId!"));
                return;
            }

            Integer customerId = Integer.parseInt(customerIdParam);
            List<BookingDto> bookings = bookingService.getBookingsByCustomer(customerId);

            response.setStatus(HttpServletResponse.SC_OK);
            objectMapper.writeValue(response.getWriter(), bookings);

        } catch (Exception e) {
            response.setStatus(HttpServletResponse.SC_INTERNAL_SERVER_ERROR);
            objectMapper.writeValue(response.getWriter(), Map.of("error", "Помилка сервера: " + e.getMessage()));
        }
    }

    // створення нового бронювання
    @Override
    protected void doPost(HttpServletRequest request, HttpServletResponse response) throws IOException {
        response.setContentType("application/json");
        response.setCharacterEncoding("UTF-8");

        try {
            BookingDto bookingDto = objectMapper.readValue(request.getInputStream(), BookingDto.class);
            BookingDto savedBooking = bookingService.createBooking(bookingDto);

            response.setStatus(HttpServletResponse.SC_CREATED);
            objectMapper.writeValue(response.getWriter(), savedBooking);

        } catch (Exception e) {
            response.setStatus(HttpServletResponse.SC_INTERNAL_SERVER_ERROR);
            objectMapper.writeValue(response.getWriter(), Map.of("error", "Помилка сервера: " + e.getMessage()));
        }
    }
}
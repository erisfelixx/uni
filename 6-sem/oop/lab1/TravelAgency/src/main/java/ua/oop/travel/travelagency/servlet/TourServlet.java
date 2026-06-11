package ua.oop.travel.travelagency.servlet;

import com.fasterxml.jackson.databind.ObjectMapper;
import jakarta.servlet.annotation.WebServlet;
import jakarta.servlet.http.HttpServlet;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import ua.oop.travel.travelagency.dto.TourDto;
import ua.oop.travel.travelagency.service.TourService;

import java.io.IOException;
import java.util.List;
import java.util.Map;

@WebServlet("/api/tours")
public class TourServlet extends HttpServlet {

    private final TourService tourService = new TourService();
    private final ObjectMapper objectMapper = new ObjectMapper();

    // обробка GET-запитів (отримання списку турів)
    @Override
    protected void doGet(HttpServletRequest request, HttpServletResponse response) throws IOException {
        response.setContentType("application/json");
        response.setCharacterEncoding("UTF-8");

        try {
            List<TourDto> tours = tourService.getAllTours();
            response.setStatus(HttpServletResponse.SC_OK);
            objectMapper.writeValue(response.getWriter(), tours);
        } catch (Exception e) {
            response.setStatus(HttpServletResponse.SC_INTERNAL_SERVER_ERROR);
            objectMapper.writeValue(response.getWriter(), Map.of("error", "Помилка сервера: " + e.getMessage()));
        }
    }

    // обробка POST-запитів (створення нового туру)
    @Override
    protected void doPost(HttpServletRequest request, HttpServletResponse response) throws IOException {
        response.setContentType("application/json");
        response.setCharacterEncoding("UTF-8");

        try {
            TourDto tourDto = objectMapper.readValue(request.getInputStream(), TourDto.class);

            TourDto savedTour = tourService.createTour(tourDto);

            response.setStatus(HttpServletResponse.SC_CREATED);
            objectMapper.writeValue(response.getWriter(), savedTour);

        } catch (Exception e) {
            response.setStatus(HttpServletResponse.SC_INTERNAL_SERVER_ERROR);
            objectMapper.writeValue(response.getWriter(), Map.of("error", "Помилка сервера: " + e.getMessage()));
        }
    }
}
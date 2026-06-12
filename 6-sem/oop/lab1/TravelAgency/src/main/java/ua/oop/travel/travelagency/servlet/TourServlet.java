package ua.oop.travel.travelagency.servlet;

import com.fasterxml.jackson.databind.ObjectMapper;
import jakarta.servlet.annotation.WebServlet;
import jakarta.servlet.http.HttpServlet;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;
import ua.oop.travel.travelagency.dto.TourDto;
import ua.oop.travel.travelagency.service.TourService;

import java.io.IOException;
import java.util.List;
import java.util.Map;

@WebServlet("/api/tours")
public class TourServlet extends HttpServlet {

    private static final Logger logger = LogManager.getLogger(TourServlet.class);
    private final TourService tourService = new TourService();
    private final ObjectMapper objectMapper = new ObjectMapper();

    // обробка GET-запитів (отримання списку турів)
    @Override
    protected void doGet(HttpServletRequest request, HttpServletResponse response) throws IOException {
        response.setContentType("application/json");
        response.setCharacterEncoding("UTF-8");

        try {
            logger.info("Отримано запит на список усіх турів");
            List<TourDto> tours = tourService.getAllTours();

            response.setStatus(HttpServletResponse.SC_OK);
            objectMapper.writeValue(response.getWriter(), tours);
            logger.info("Успішно повернуто {} турів", tours.size());

        } catch (Exception e) {
            logger.error("Помилка під час отримання турів", e);
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
            // читаємо роль з атрибутів запиту, яку туди поклав JWTFilter
            String userRole = (String) request.getAttribute("userRole");
            logger.info("Спроба створення туру користувачем з роллю: {}", userRole);

            // перевіряємо, чи має користувач права на створення туру (тільки agent або admin)
            if (!"AGENT".equals(userRole) && !"ADMIN".equals(userRole)) {
                logger.warn("Відмовлено в доступі. Роль {} не має прав на створення туру", userRole);
                response.setStatus(HttpServletResponse.SC_FORBIDDEN);
                objectMapper.writeValue(response.getWriter(), Map.of("error", "Доступ заборонено! Тільки турагенти можуть створювати тури."));
                return;
            }

            TourDto tourDto = objectMapper.readValue(request.getInputStream(), TourDto.class);
            TourDto savedTour = tourService.createTour(tourDto);

            response.setStatus(HttpServletResponse.SC_CREATED);
            objectMapper.writeValue(response.getWriter(), savedTour);
            logger.info("Успішно створено новий тур з ID: {}", savedTour.getId());

        } catch (Exception e) {
            logger.error("Помилка під час створення туру", e);
            response.setStatus(HttpServletResponse.SC_INTERNAL_SERVER_ERROR);
            objectMapper.writeValue(response.getWriter(), Map.of("error", "Помилка сервера: " + e.getMessage()));
        }
    }
}
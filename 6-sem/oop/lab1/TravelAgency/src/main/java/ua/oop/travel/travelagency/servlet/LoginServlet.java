package ua.oop.travel.travelagency.servlet;

import com.fasterxml.jackson.databind.ObjectMapper;
import jakarta.servlet.annotation.WebServlet;
import jakarta.servlet.http.HttpServlet;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import ua.oop.travel.travelagency.dto.AuthResponseDto;
import ua.oop.travel.travelagency.service.UserService;

import java.io.IOException;
import java.util.Map;
import java.util.Optional;

@WebServlet("/api/auth/login")
public class LoginServlet extends HttpServlet {

    private final UserService userService = new UserService();
    private final ObjectMapper objectMapper = new ObjectMapper();

    @Override
    protected void doPost(HttpServletRequest request, HttpServletResponse response) throws IOException {
        response.setContentType("application/json");
        response.setCharacterEncoding("UTF-8");

        try {
            // читаємо email та password з тіла запиту
            Map<?, ?> jsonMap = objectMapper.readValue(request.getInputStream(), Map.class);
            String email = (String) jsonMap.get("email");
            String password = (String) jsonMap.get("password");

            // викликаємо аутентифікацію
            Optional<AuthResponseDto> authResult = userService.authenticate(email, password);

            if (authResult.isPresent()) {
                // якщо все добре - повертаємо 200 OK та дані з токеном
                response.setStatus(HttpServletResponse.SC_OK);
                objectMapper.writeValue(response.getWriter(), authResult.get());
            } else {
                // якщо пароль чи email невірні - 401 Unauthorized
                response.setStatus(HttpServletResponse.SC_UNAUTHORIZED);
                objectMapper.writeValue(response.getWriter(), Map.of("error", "Невірний email або пароль!"));
            }

        } catch (Exception e) {
            response.setStatus(HttpServletResponse.SC_INTERNAL_SERVER_ERROR);
            objectMapper.writeValue(response.getWriter(), Map.of("error", "Помилка сервера: " + e.getMessage()));
        }
    }
}
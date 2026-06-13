package ua.oop.travel.travelagency.servlet;

import com.fasterxml.jackson.databind.ObjectMapper;
import jakarta.servlet.annotation.WebServlet;
import jakarta.servlet.http.HttpServlet;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import ua.oop.travel.travelagency.dto.UserDto;
import ua.oop.travel.travelagency.service.UserService;

import java.io.IOException;
import java.util.Map;

//ендпоінт, на який Angular буде штовхати POST-запит
@WebServlet("/api/auth/register")
public class RegisterServlet extends HttpServlet {

    private final UserService userService = new UserService();
    private final ObjectMapper objectMapper = new ObjectMapper();

    @Override
    protected void doPost(HttpServletRequest request, HttpServletResponse response) throws IOException {
        //правильні кодування та тип контенту (JSON)
        response.setContentType("application/json");
        response.setCharacterEncoding("UTF-8");

        try {
            Map<?, ?> jsonMap = objectMapper.readValue(request.getInputStream(), Map.class);

            String fullName = (String) jsonMap.get("fullName");
            String email = (String) jsonMap.get("email");
            String password = (String) jsonMap.get("password");
            String role = (String) jsonMap.get("role");

            UserDto registeredUser = userService.registerUser(fullName, email, password, role);

            response.setStatus(HttpServletResponse.SC_CREATED);
            objectMapper.writeValue(response.getWriter(), registeredUser);

        } catch (IllegalArgumentException e) {
            // якщо користувач вже існує або дані невалідні
            response.setStatus(HttpServletResponse.SC_BAD_REQUEST);
            objectMapper.writeValue(response.getWriter(), Map.of("error", e.getMessage()));
        } catch (Exception e) {
            // якщо щось впало на рівні бд
            response.setStatus(HttpServletResponse.SC_INTERNAL_SERVER_ERROR);
            objectMapper.writeValue(response.getWriter(), Map.of("error", "Помилка сервера: " + e.getMessage()));
        }
    }
}
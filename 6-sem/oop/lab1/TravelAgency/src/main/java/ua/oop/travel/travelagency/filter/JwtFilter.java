package ua.oop.travel.travelagency.filter;

import com.auth0.jwt.exceptions.JWTVerificationException;
import com.auth0.jwt.interfaces.DecodedJWT;
import jakarta.servlet.*;
import jakarta.servlet.annotation.WebFilter;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;
import ua.oop.travel.travelagency.service.JwtUtil;

import java.io.IOException;

@WebFilter(urlPatterns = {"/api/tours/*", "/api/bookings/*"})
public class JwtFilter implements Filter {

    private static final Logger logger = LogManager.getLogger(JwtFilter.class);

    @Override
    public void doFilter(ServletRequest request, ServletResponse response, FilterChain chain)
            throws IOException, ServletException {

        HttpServletRequest httpRequest = (HttpServletRequest) request;
        HttpServletResponse httpResponse = (HttpServletResponse) response;

        // якщо це GET-запит для турів — дозволяємо доступ без токена
        if (httpRequest.getMethod().equalsIgnoreCase("GET") && httpRequest.getRequestURI().contains("/api/tours")) {
            logger.info("Публічний доступ до GET /api/tours");
            chain.doFilter(request, response);
            return;
        }

        String authHeader = httpRequest.getHeader("Authorization");

        if (authHeader != null && authHeader.startsWith("Bearer ")) {
            String token = authHeader.substring(7); // щоб отримати чистий токен

            try {
                // валідуємо токен та отримуємо його розшифрований вміст
                DecodedJWT decodedJWT = JwtUtil.verifyToken(token);

                // дістаємо роль та ID з токена і кладемо їх в атрибути запиту
                String role = decodedJWT.getClaim("role").asString();
                request.setAttribute("userRole", role);
                request.setAttribute("userId", decodedJWT.getClaim("id").asInt());

                logger.info("Авторизація успішна для ролі: {}", role);
                // якщо помилки не виникло - токен валідний - пускаємо запит далі до сервлета
                chain.doFilter(request, response);
                return;

            } catch (JWTVerificationException e) {
                logger.warn("Недійсний або прострочений JWT токен: {}", e.getMessage());
                // якщо токен прострочений або підроблений
                httpResponse.setStatus(HttpServletResponse.SC_UNAUTHORIZED);
                httpResponse.setContentType("application/json");
                httpResponse.setCharacterEncoding("UTF-8");
                httpResponse.getWriter().write("{\"error\": \"Токен недійсний або прострочений!\"}");
                return;
            }
        }

        logger.warn("Відсутній заголовок Authorization у запиті до {}", httpRequest.getRequestURI());
        // якщо заголовка взагалі немає
        httpResponse.setStatus(HttpServletResponse.SC_UNAUTHORIZED);
        httpResponse.setContentType("application/json");
        httpResponse.setCharacterEncoding("UTF-8");
        httpResponse.getWriter().write("{\"error\": \"Відсутній токен авторизації!\"}");
    }
}
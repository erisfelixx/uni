package ua.oop.travel.travelagency.filter;

import com.auth0.jwt.exceptions.JWTVerificationException;
import jakarta.servlet.*;
import jakarta.servlet.annotation.WebFilter;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import ua.oop.travel.travelagency.service.JwtUtil;

import java.io.IOException;

@WebFilter(urlPatterns = {"/api/tours/*", "/api/bookings/*"})
public class JwtFilter implements Filter {

    @Override
    public void doFilter(ServletRequest request, ServletResponse response, FilterChain chain)
            throws IOException, ServletException {

        HttpServletRequest httpRequest = (HttpServletRequest) request;
        HttpServletResponse httpResponse = (HttpServletResponse) response;

        // якщо це GET-запит для турів — дозволяємо доступ без токена
        if (httpRequest.getMethod().equalsIgnoreCase("GET") && httpRequest.getRequestURI().contains("/api/tours")) {
            chain.doFilter(request, response);
            return;
        }

        String authHeader = httpRequest.getHeader("Authorization");

        if (authHeader != null && authHeader.startsWith("Bearer ")) {
            String token = authHeader.substring(7); // щоб отримати чистий токен

            try {
                JwtUtil.verifyToken(token);
                // якщо помилки не виникло - токен валідний - пускаємо запит далі до сервлета
                chain.doFilter(request, response);
                return;

            } catch (JWTVerificationException e) {
                // якщо токен прострочений або підроблений
                httpResponse.setStatus(HttpServletResponse.SC_UNAUTHORIZED);
                httpResponse.setContentType("application/json");
                httpResponse.setCharacterEncoding("UTF-8");
                httpResponse.getWriter().write("{\"error\": \"Токен недійсний або прострочений!\"}");
                return;
            }
        }

        // якщо заголовка взагалі немає
        httpResponse.setStatus(HttpServletResponse.SC_UNAUTHORIZED);
        httpResponse.setContentType("application/json");
        httpResponse.setCharacterEncoding("UTF-8");
        httpResponse.getWriter().write("{\"error\": \"Відсутній токен авторизації!\"}");
    }
}
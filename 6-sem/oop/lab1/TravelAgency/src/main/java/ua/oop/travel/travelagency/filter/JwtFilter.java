package ua.oop.travel.travelagency.filter;

import com.auth0.jwt.exceptions.JWTVerificationException;
import com.auth0.jwt.interfaces.DecodedJWT;
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
                // валідуємо токен та отримуємо його розшифрований вміст
                DecodedJWT decodedJWT = JwtUtil.verifyToken(token);

                // дістаємо роль та id з токена і кладемо їх в атрибути запиту
                request.setAttribute("userRole", decodedJWT.getClaim("role").asString());
                request.setAttribute("userId", decodedJWT.getClaim("id").asInt());

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
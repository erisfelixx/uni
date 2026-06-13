package ua.oop.travel.travelagency.filter;

import jakarta.servlet.*;
import jakarta.servlet.annotation.WebFilter;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;

import java.io.IOException;

// застосовуємо цей фільтр абсолютно до всіх запитів, що йдуть на наш API
@WebFilter("/*")
public class CorsFilter implements Filter {

    @Override
    public void doFilter(ServletRequest request, ServletResponse response, FilterChain chain)
            throws IOException, ServletException {

        HttpServletRequest httpRequest = (HttpServletRequest) request;
        HttpServletResponse httpResponse = (HttpServletResponse) response;

        // дозволяємо доступ тільки нашому React-додатку
        httpResponse.setHeader("Access-Control-Allow-Origin", "http://localhost:5173");

        // дозволяємо всі основні HTTP-методи
        httpResponse.setHeader("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS");

        // дозволяємо передавати специфічні заголовки (наприклад, Authorization для нашого JWT-токена)
        httpResponse.setHeader("Access-Control-Allow-Headers", "Content-Type, Authorization");

        // дозволяємо передачу credentials (необхідно для деяких конфігурацій axios)
        httpResponse.setHeader("Access-Control-Allow-Credentials", "true");

        // браузери перед POST-запитом завжди відправляють попередній OPTIONS-запит (preflight)
        // ми маємо миттєво відповісти на нього статусом 200 OK і зупинити ланцюжок
        if ("OPTIONS".equalsIgnoreCase(httpRequest.getMethod())) {
            httpResponse.setStatus(HttpServletResponse.SC_OK);
            return;
        }

        // пускаємо запит далі до інших фільтрів (наприклад, JwtFilter) та сервлетів
        chain.doFilter(request, response);
    }
}
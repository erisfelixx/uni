package ua.oop.travel.travelagency.servlet;

import jakarta.servlet.ServletInputStream;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import ua.oop.travel.travelagency.dto.TourDto;
import ua.oop.travel.travelagency.service.TourService;

import java.io.ByteArrayInputStream;
import java.io.IOException;
import java.io.PrintWriter;
import java.io.StringWriter;
import java.util.List;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class TourServletTest {

    @Mock
    private TourService tourService;

    @Mock
    private HttpServletRequest request;

    @Mock
    private HttpServletResponse response;

    @InjectMocks
    private TourServlet tourServlet;

    // допоміжний метод для імітації JSON-тіла запиту
    private void mockRequestBody(String json) throws IOException {
        ByteArrayInputStream byteArrayInputStream = new ByteArrayInputStream(json.getBytes());
        ServletInputStream servletInputStream = new ServletInputStream() {
            @Override public int read() { return byteArrayInputStream.read(); }
            @Override public boolean isFinished() { return byteArrayInputStream.available() == 0; }
            @Override public boolean isReady() { return true; }
            @Override public void setReadListener(jakarta.servlet.ReadListener readListener) {}
        };
        when(request.getInputStream()).thenReturn(servletInputStream);
    }

    // ТЕСТ 1: Перевірка GET-запиту (отримання списку)
    @Test
    void doGet_Returns200_AndTourList() throws Exception {
        StringWriter stringWriter = new StringWriter();
        when(response.getWriter()).thenReturn(new PrintWriter(stringWriter));

        // вчимо сервіс повертати список з одним "фейковим" туром
        when(tourService.getAllTours()).thenReturn(List.of(new TourDto()));

        tourServlet.doGet(request, response);

        // перевіряємо, чи статус 200 OK
        verify(response).setStatus(HttpServletResponse.SC_OK);
    }

    // ТЕСТ 2: Перевірка POST-запиту від звичайного клієнта (має бути заборонено)
    @Test
    void doPost_CustomerRole_Returns403Forbidden() throws Exception {
        StringWriter stringWriter = new StringWriter();
        when(response.getWriter()).thenReturn(new PrintWriter(stringWriter));

        // імітуємо, що запит робить звичайний клієнт
        when(request.getAttribute("userRole")).thenReturn("CUSTOMER");

        tourServlet.doPost(request, response);

        // перевіряємо, чи спрацював захист і повернув 403 FORBIDDEN
        verify(response).setStatus(HttpServletResponse.SC_FORBIDDEN);

        // переконуємося, що метод створення туру НЕ викликався взагалі
        verify(tourService, never()).createTour(any());
    }

    // ТЕСТ 3: Перевірка POST-запиту від агента (має бути дозволено)
    @Test
    void doPost_AgentRole_Returns201Created() throws Exception {
        StringWriter stringWriter = new StringWriter();
        when(response.getWriter()).thenReturn(new PrintWriter(stringWriter));

        // імітуємо, що запит робить агент
        when(request.getAttribute("userRole")).thenReturn("AGENT");

        // імітуємо правильне тіло запиту
        mockRequestBody("{\"title\":\"Test Tour\",\"basePrice\":1000.00}");

        // вчимо сервіс повертати збережений об'єкт
        when(tourService.createTour(any(TourDto.class))).thenReturn(new TourDto());

        tourServlet.doPost(request, response);

        // перевіряємо, чи тур успішно створено зі статусом 201 CREATED
        verify(response).setStatus(HttpServletResponse.SC_CREATED);
    }
}
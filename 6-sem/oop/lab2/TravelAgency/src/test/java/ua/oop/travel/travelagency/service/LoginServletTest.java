package ua.oop.travel.travelagency.servlet;

import jakarta.servlet.ServletInputStream;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import ua.oop.travel.travelagency.dto.AuthResponseDto;
import ua.oop.travel.travelagency.service.UserService;

import java.io.ByteArrayInputStream;
import java.io.IOException;
import java.io.PrintWriter;
import java.io.StringWriter;
import java.util.Optional;

import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class LoginServletTest {

    @Mock
    private UserService userService;

    @Mock
    private HttpServletRequest request;

    @Mock
    private HttpServletResponse response;

    @InjectMocks
    private LoginServlet loginServlet;

    // cпеціальний допоміжний метод, який імітує те, що користувач надсилає JSON з фронтенду
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

    @Test
    void doPost_SuccessfulLogin_Returns200() throws Exception {
        // 1. ПІДГОТОВКА (Arrange)
        // імітуємо запит від фронтенду з правильними даними
        mockRequestBody("{\"email\":\"anna@test.com\",\"password\":\"1234\"}");

        // імітуємо об'єкт для запису відповіді (щоб сервлет не впав з помилкою)
        StringWriter stringWriter = new StringWriter();
        when(response.getWriter()).thenReturn(new PrintWriter(stringWriter));

        // вчимо наш сервіс: якщо прийшли ці пошта і пароль, відповідай, що користувач знайдений
        AuthResponseDto mockAuthResponse = mock(AuthResponseDto.class);
        when(userService.authenticate("anna@test.com", "1234")).thenReturn(Optional.of(mockAuthResponse));

        // 2. ВИКОНАННЯ (Act)
        loginServlet.doPost(request, response);

        // 3. ПЕРЕВІРКА (Assert)
        // перевіряємо, чи сервлет дійсно встановив статус 200 OK
        verify(response).setStatus(HttpServletResponse.SC_OK);
    }

    @Test
    void doPost_FailedLogin_Returns401() throws Exception {
        // 1. ПІДГОТОВКА (Arrange)
        // імітуємо запит від фронтенду з НЕПРАВИЛЬНИМ паролем
        mockRequestBody("{\"email\":\"anna@test.com\",\"password\":\"wrong_password\"}");

        StringWriter stringWriter = new StringWriter();
        when(response.getWriter()).thenReturn(new PrintWriter(stringWriter));

        // вчимо сервіс: якщо пароль неправильний, повертай порожній результат
        when(userService.authenticate("anna@test.com", "wrong_password")).thenReturn(Optional.empty());

        // 2. ВИКОНАННЯ (Act)
        loginServlet.doPost(request, response);

        // 3. ПЕРЕВІРКА (Assert)
        // перевіряємо, чи сервлет захистив систему і видав статус 401 UNAUTHORIZED
        verify(response).setStatus(HttpServletResponse.SC_UNAUTHORIZED);
    }
}
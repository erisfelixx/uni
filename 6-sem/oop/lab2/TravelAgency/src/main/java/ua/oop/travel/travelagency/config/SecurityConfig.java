package ua.oop.travel.travelagency.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.HttpMethod;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.config.annotation.web.configurers.AbstractHttpConfigurer;
import org.springframework.security.config.http.SessionCreationPolicy;
import org.springframework.security.web.SecurityFilterChain;

@Configuration
@EnableWebSecurity
public class SecurityConfig {

    @Bean
    public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
        http
                // вимикаємо захист CSRF, оскільки у нас REST API з токенами
                .csrf(AbstractHttpConfigurer::disable)

                // робимо сесії "stateless" (без стану), бо стан зберігається в JWT токені
                .sessionManagement(session -> session.sessionCreationPolicy(SessionCreationPolicy.STATELESS))

                // налаштовуємо правила доступу
                .authorizeHttpRequests(auth -> auth
                        .requestMatchers(HttpMethod.OPTIONS, "/**").permitAll() // дозволяємо CORS-запити
                        .requestMatchers(HttpMethod.GET, "/api/tours/**").permitAll() // переглядати тури можуть усі
                        .requestMatchers("/api/bookings/**").authenticated() // бронювати можуть тільки авторизовані
                        // для простоти поки вимагаємо просто авторизацію, ролі можна докрутити пізніше
                        .requestMatchers("/api/discounts/**").authenticated()
                        .anyRequest().permitAll()
                )

                // вмикаємо перевірку JWT токенів (Keycloak)
                .oauth2ResourceServer(oauth2 -> oauth2.jwt(jwt -> {}));

        return http.build();
    }
}
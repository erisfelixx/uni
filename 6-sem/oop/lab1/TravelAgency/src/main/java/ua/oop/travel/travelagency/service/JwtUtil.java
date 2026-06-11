package ua.oop.travel.travelagency.service;

import com.auth0.jwt.JWT;
import com.auth0.jwt.algorithms.Algorithm;
import ua.oop.travel.travelagency.dto.UserDto;

import java.util.Date;

public class JwtUtil {
    // секретний ключ для шифрування токена
    private static final String SECRET = "my_super_secret_travel_agency_key_12345";
    private static final Algorithm ALGORITHM = Algorithm.HMAC256(SECRET);

    // токен буде дійсний протягом 24 годин
    private static final long EXPIRATION_TIME = 86_400_000;

    public static String generateToken(UserDto user) {
        return JWT.create()
                .withSubject(user.getEmail())
                .withClaim("id", user.getId())
                .withClaim("role", user.getRole())
                .withClaim("fullName", user.getFullName())
                .withIssuedAt(new Date()) // час створення
                .withExpiresAt(new Date(System.currentTimeMillis() + EXPIRATION_TIME)) // час завершення дії
                .sign(ALGORITHM);
    }
}
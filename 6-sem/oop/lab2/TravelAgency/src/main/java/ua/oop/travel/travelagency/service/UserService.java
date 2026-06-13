package ua.oop.travel.travelagency.service;

import ua.oop.travel.travelagency.dao.UserDao;
import ua.oop.travel.travelagency.dto.AuthResponseDto;
import ua.oop.travel.travelagency.dto.UserDto;
import ua.oop.travel.travelagency.mapper.UserMapper;
import ua.oop.travel.travelagency.model.User;

import java.sql.SQLException;
import java.util.Optional;

public class UserService {
    private final UserDao userDao = new UserDao();
    private final UserMapper userMapper = UserMapper.INSTANCE;

    // реєстрація нового користувача
    public UserDto registerUser(String fullName, String email, String password, String role) throws SQLException {
        // перевірка чи такий email вже зайнятий
        if (userDao.findByEmail(email).isPresent()) {
            throw new IllegalArgumentException("Користувач з таким email вже існує!");
        }

        // хеш пароля
        String passwordHash = String.valueOf(password.hashCode());

        User user = User.builder()
                .fullName(fullName)
                .email(email)
                .passwordHash(passwordHash)
                .role(role != null ? role : "CUSTOMER")
                .build();

        User savedUser = userDao.save(user);
        return userMapper.toDto(savedUser); //повертаємо безпечний DTO без пароля
    }

    // логін користувача
    public Optional<UserDto> login(String email, String password) throws SQLException {
        Optional<User> userOpt = userDao.findByEmail(email);

        if (userOpt.isPresent()) {
            User user = userOpt.get();
            String targetHash = String.valueOf(password.hashCode());

            // якщо хеші паролів збігаються - повертаємо DTO
            if (user.getPasswordHash().equals(targetHash)) {
                return Optional.of(userMapper.toDto(user));
            }
        }
        return Optional.empty();
    }

    // метод для повної аутентифікації користувача (з генерацією JWT токена)
    public Optional<AuthResponseDto> authenticate(String email, String password) throws SQLException {
        Optional<UserDto> userDtoOpt = login(email, password); // викликаємо наш старий метод перевірки

        if (userDtoOpt.isPresent()) {
            UserDto userDto = userDtoOpt.get();
            // якщо логін успішний — генеруємо токен
            String token = JwtUtil.generateToken(userDto);
            // повертаємо DTO разом із токеном
            return Optional.of(new AuthResponseDto(userDto, token));
        }
        return Optional.empty();
    }
}
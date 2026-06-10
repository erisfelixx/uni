package ua.oop.travel.travelagency.dao;

import ua.oop.travel.travelagency.model.User;

import java.sql.*;
import java.util.Optional;

public class UserDao {

    // 1. Збереження нового користувача (реєстрація)
    public User save(User user) throws SQLException {
        String sql = "INSERT INTO users (full_name, email, password_hash, role) VALUES (?, ?, ?, ?)";

        try (Connection connection = DatabaseConnection.getInstance().getConnection();
             PreparedStatement statement = connection.prepareStatement(sql, Statement.RETURN_GENERATED_KEYS)) {

            statement.setString(1, user.getFullName());
            statement.setString(2, user.getEmail());
            statement.setString(3, user.getPasswordHash());
            statement.setString(4, user.getRole());

            statement.executeUpdate();

            // отримуємо згенерований базою ID і записуємо його в наш об'єкт
            try (ResultSet generatedKeys = statement.getGeneratedKeys()) {
                if (generatedKeys.next()) {
                    user.setId(generatedKeys.getInt(1));
                }
            }
            return user;
        }
    }

    // 2. Пошук користувача за email (для логіну й валідації)
    public Optional<User> findByEmail(String email) throws SQLException {
        String sql = "SELECT * FROM users WHERE email = ?";

        try (Connection connection = DatabaseConnection.getInstance().getConnection();
             PreparedStatement statement = connection.prepareStatement(sql)) {

            statement.setString(1, email);

            try (ResultSet resultSet = statement.executeQuery()) {
                if (resultSet.next()) {
                    User user = User.builder()
                            .id(resultSet.getInt("id"))
                            .fullName(resultSet.getString("full_name"))
                            .email(resultSet.getString("email"))
                            .passwordHash(resultSet.getString("password_hash"))
                            .role(resultSet.getString("role"))
                            .build();
                    return Optional.of(user);
                }
            }
        }
        //(щоб уникнути NullPointerException)
        return Optional.empty();
    }
}
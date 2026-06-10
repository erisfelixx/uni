package ua.oop.travel.travelagency.dao;

import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.SQLException;

public class DatabaseConnection {
    // статична змінна, зберігає єдиний екземпляр нашого підключення
    private static DatabaseConnection instance;
    private Connection connection;

    private final String URL = "jdbc:postgresql://localhost:5432/annasovhyria";
    private final String USER = "annasovhyria";
    private final String PASSWORD = "";

    private DatabaseConnection() throws SQLException {
        try {
            // реєструємо драйвер
            Class.forName("org.postgresql.Driver");
            this.connection = DriverManager.getConnection(URL, USER, PASSWORD);
        } catch (ClassNotFoundException e) {
            throw new SQLException("PostgreSQL Driver не знайдено!", e);
        }
    }

    // синхронізований метод для потокобезпечності
    public static synchronized DatabaseConnection getInstance() throws SQLException {
        if (instance == null || instance.getConnection().isClosed()) {
            instance = new DatabaseConnection();
        }
        return instance;
    }

    public Connection getConnection() {
        return connection;
    }
}
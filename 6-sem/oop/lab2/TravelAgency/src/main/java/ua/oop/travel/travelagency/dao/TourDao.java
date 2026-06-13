package ua.oop.travel.travelagency.dao;

import ua.oop.travel.travelagency.model.Tour;
import java.sql.*;
import java.util.ArrayList;
import java.util.List;

public class TourDao {

    // отримати список усіх турів
    public List<Tour> findAll() throws SQLException {
        List<Tour> tours = new ArrayList<>();
        String sql = "SELECT * FROM tours";

        try (Connection conn = DatabaseConnection.getInstance().getConnection();
             Statement stmt = conn.createStatement();
             ResultSet rs = stmt.executeQuery(sql)) {

            while (rs.next()) {
                tours.add(mapResultSetToTour(rs));
            }
        }
        return tours;
    }

    // зберегти новий тур у базу даних
    public Tour save(Tour tour) throws SQLException {
        String sql = "INSERT INTO tours (title, description, tour_type, base_price, is_hot) VALUES (?, ?, ?, ?, ?) RETURNING id";

        try (Connection conn = DatabaseConnection.getInstance().getConnection();
             PreparedStatement pstmt = conn.prepareStatement(sql)) {

            pstmt.setString(1, tour.getTitle());
            pstmt.setString(2, tour.getDescription());
            pstmt.setString(3, tour.getTourType());
            pstmt.setBigDecimal(4, tour.getBasePrice());
            pstmt.setBoolean(5, tour.getIsHot());

            try (ResultSet rs = pstmt.executeQuery()) {
                if (rs.next()) {
                    tour.setId(rs.getInt("id"));
                }
            }
        }
        return tour;
    }

    // мапінг рядка з БД в об'єкт Java
    private Tour mapResultSetToTour(ResultSet rs) throws SQLException {
        return Tour.builder()
                .id(rs.getInt("id"))
                .title(rs.getString("title"))
                .description(rs.getString("description"))
                .tourType(rs.getString("tour_type"))
                .basePrice(rs.getBigDecimal("base_price"))
                .isHot(rs.getBoolean("is_hot"))
                .build();
    }
}
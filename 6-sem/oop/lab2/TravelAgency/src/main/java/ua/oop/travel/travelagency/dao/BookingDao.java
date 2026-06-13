package ua.oop.travel.travelagency.dao;

import ua.oop.travel.travelagency.model.Booking;
import java.sql.*;
import java.util.ArrayList;
import java.util.List;

public class BookingDao {

    // збереження нового бронювання
    public Booking save(Booking booking) throws SQLException {
        String sql = "INSERT INTO bookings (customer_id, tour_id, status, final_price, created_at) VALUES (?, ?, ?, ?, ?) RETURNING id";

        try (Connection conn = DatabaseConnection.getInstance().getConnection();
             PreparedStatement pstmt = conn.prepareStatement(sql)) {

            pstmt.setInt(1, booking.getCustomerId());
            pstmt.setInt(2, booking.getTourId());
            pstmt.setString(3, booking.getStatus());
            pstmt.setBigDecimal(4, booking.getFinalPrice());
            // перетворюємо LocalDateTime з Java у Timestamp для PostgreSQL
            pstmt.setTimestamp(5, Timestamp.valueOf(booking.getCreatedAt()));

            try (ResultSet rs = pstmt.executeQuery()) {
                if (rs.next()) {
                    booking.setId(rs.getInt("id"));
                }
            }
        }
        return booking;
    }

    // отримання списку бронювань конкретного користувача (по customer_id)
    public List<Booking> findAllByCustomerId(Integer customerId) throws SQLException {
        List<Booking> bookings = new ArrayList<>();
        String sql = "SELECT * FROM bookings WHERE customer_id = ?";

        try (Connection conn = DatabaseConnection.getInstance().getConnection();
             PreparedStatement pstmt = conn.prepareStatement(sql)) {

            pstmt.setInt(1, customerId);

            try (ResultSet rs = pstmt.executeQuery()) {
                while (rs.next()) {
                    bookings.add(Booking.builder()
                            .id(rs.getInt("id"))
                            .customerId(rs.getInt("customer_id"))
                            .tourId(rs.getInt("tour_id"))
                            .status(rs.getString("status"))
                            .finalPrice(rs.getBigDecimal("final_price"))
                            .createdAt(rs.getTimestamp("created_at").toLocalDateTime())
                            .build());
                }
            }
        }
        return bookings;
    }
}
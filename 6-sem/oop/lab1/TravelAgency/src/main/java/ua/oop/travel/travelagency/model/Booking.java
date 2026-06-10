package ua.oop.travel.travelagency.model;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.math.BigDecimal;
import java.time.LocalDateTime;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class Booking {
    private Integer id;
    private Integer customerId;
    private Integer tourId;
    private String status; // 'PENDING', 'PAID', 'CANCELLED'
    private BigDecimal finalPrice;
    private LocalDateTime createdAt;
}
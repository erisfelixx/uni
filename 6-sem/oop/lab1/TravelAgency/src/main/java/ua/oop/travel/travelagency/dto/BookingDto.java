package ua.oop.travel.travelagency.dto;

import lombok.Data;
import java.math.BigDecimal;
import java.time.LocalDateTime;

@Data
public class BookingDto {
    private Integer id;
    private Integer customerId;
    private Integer tourId;
    private String status;
    private BigDecimal finalPrice;
    private LocalDateTime createdAt;
}
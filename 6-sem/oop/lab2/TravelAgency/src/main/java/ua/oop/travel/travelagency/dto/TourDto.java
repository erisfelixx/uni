package ua.oop.travel.travelagency.dto;

import lombok.Data;
import java.math.BigDecimal;

@Data
public class TourDto {
    private Integer id;
    private String title;
    private String description;
    private String tourType;
    private BigDecimal basePrice;
    private Boolean isHot;
}
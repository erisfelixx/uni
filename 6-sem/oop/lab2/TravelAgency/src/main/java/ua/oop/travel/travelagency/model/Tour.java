package ua.oop.travel.travelagency.model;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.math.BigDecimal;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class Tour {
    private Integer id;
    private String title;
    private String description;
    private String tourType; // 'REST', 'EXCURSION', або 'SHOPPING'
    private BigDecimal basePrice;
    private Boolean isHot;
}
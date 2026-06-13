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
public class Discount {
    private Integer id;
    private Integer userId;
    private BigDecimal discountPercentage;
}
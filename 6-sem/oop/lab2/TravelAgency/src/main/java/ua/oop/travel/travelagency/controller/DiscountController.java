package ua.oop.travel.travelagency.controller;

import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import ua.oop.travel.travelagency.entity.Discount;
import ua.oop.travel.travelagency.service.DiscountService;

import java.math.BigDecimal;

@RestController
@RequestMapping("/api/discounts")
@CrossOrigin
@RequiredArgsConstructor
public class DiscountController {

    private final DiscountService discountService;

    @PostMapping
    public ResponseEntity<Discount> setDiscount(@RequestParam Integer userId, @RequestParam BigDecimal percentage) {
        return ResponseEntity.ok(discountService.setDiscount(userId, percentage));
    }
}
package ua.oop.travel.travelagency.service;

import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import ua.oop.travel.travelagency.entity.Discount;
import ua.oop.travel.travelagency.entity.User;
import ua.oop.travel.travelagency.repository.DiscountRepository;
import ua.oop.travel.travelagency.repository.UserRepository;

import java.math.BigDecimal;

@Service
@RequiredArgsConstructor
public class DiscountService {

    private final DiscountRepository discountRepository;
    private final UserRepository userRepository;

    public Discount setDiscount(Integer userId, BigDecimal percentage) {
        User user = userRepository.findById(userId)
                .orElseThrow(() -> new RuntimeException("User not found"));

        Discount discount = discountRepository.findByUserId(userId).orElse(new Discount());
        discount.setUser(user);
        discount.setDiscountPercentage(percentage);

        return discountRepository.save(discount);
    }
}
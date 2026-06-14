package ua.oop.travel.travelagency.repository;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;
import ua.oop.travel.travelagency.entity.Payment;

@Repository
public interface PaymentRepository extends JpaRepository<Payment, Integer> {
}
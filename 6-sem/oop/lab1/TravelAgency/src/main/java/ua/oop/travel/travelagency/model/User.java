package ua.oop.travel.travelagency.model;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data // автоматично генерує getter, setter, toString, equals та hashCode
@Builder // реалізує GoF патерн "Builder" для зручного створення об'єктів
@NoArgsConstructor // генерує порожній конструктор
@AllArgsConstructor // генерує конструктор з усіма полями
public class User {
    private Integer id;
    private String fullName;
    private String email;
    private String passwordHash;
    private String role; // може бути 'CUSTOMER' або 'AGENT'
}
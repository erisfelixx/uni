package ua.oop.travel.travelagency.dto;

import lombok.AllArgsConstructor;
import lombok.Data;

@Data
@AllArgsConstructor
public class AuthResponseDto {
    private UserDto user;
    private String token;
}
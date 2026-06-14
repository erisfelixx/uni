package ua.oop.travel.travelagency.mapper;

import org.mapstruct.Mapper;
import ua.oop.travel.travelagency.dto.UserDto;
import ua.oop.travel.travelagency.entity.User;

@Mapper(componentModel = "spring")
public interface UserMapper {
    UserDto toDto(User user);
    User toModel(UserDto userDto);
}
package ua.oop.travel.travelagency.mapper;

import org.mapstruct.Mapper;
import org.mapstruct.factory.Mappers;
import ua.oop.travel.travelagency.dto.UserDto;
import ua.oop.travel.travelagency.model.User;

@Mapper
public interface UserMapper {

    UserMapper INSTANCE = Mappers.getMapper(UserMapper.class);
    UserDto toDto(User user);
    User toModel(UserDto userDto);
}
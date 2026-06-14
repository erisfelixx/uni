package ua.oop.travel.travelagency.mapper;

import org.mapstruct.Mapper;
import ua.oop.travel.travelagency.dto.TourDto;
import ua.oop.travel.travelagency.entity.Tour;

import java.util.List;

@Mapper(componentModel = "spring")
public interface TourMapper {
    TourDto toDto(Tour tour);
    Tour toModel(TourDto tourDto);
    List<TourDto> toDtoList(List<Tour> tours);
}
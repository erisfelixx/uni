package ua.oop.travel.travelagency.mapper;

import org.mapstruct.Mapper;
import org.mapstruct.factory.Mappers;
import ua.oop.travel.travelagency.dto.TourDto;
import ua.oop.travel.travelagency.model.Tour;

import java.util.List;

@Mapper
public interface TourMapper {
    TourMapper INSTANCE = Mappers.getMapper(TourMapper.class);

    TourDto toDto(Tour tour);
    Tour toModel(TourDto tourDto);
    List<TourDto> toDtoList(List<Tour> tours);
}
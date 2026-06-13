package ua.oop.travel.travelagency.mapper;

import org.mapstruct.Mapper;
import org.mapstruct.factory.Mappers;
import ua.oop.travel.travelagency.dto.BookingDto;
import ua.oop.travel.travelagency.model.Booking;
import java.util.List;

@Mapper
public interface BookingMapper {
    BookingMapper INSTANCE = Mappers.getMapper(BookingMapper.class);

    BookingDto toDto(Booking booking);
    Booking toModel(BookingDto bookingDto);
    List<BookingDto> toDtoList(List<Booking> bookings);
}
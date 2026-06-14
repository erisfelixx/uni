package ua.oop.travel.travelagency.mapper;

import org.mapstruct.Mapper;
import org.mapstruct.Mapping;
import ua.oop.travel.travelagency.dto.BookingDto;
import ua.oop.travel.travelagency.entity.Booking;

import java.util.List;

@Mapper(componentModel = "spring")
public interface BookingMapper {

    @Mapping(source = "customer.id", target = "customerId")
    @Mapping(source = "tour.id", target = "tourId")
    BookingDto toDto(Booking booking);

    @Mapping(source = "customerId", target = "customer.id")
    @Mapping(source = "tourId", target = "tour.id")
    Booking toModel(BookingDto bookingDto);

    List<BookingDto> toDtoList(List<Booking> bookings);
}
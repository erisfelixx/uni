package ua.oop.travel.travelagency.service;

import ua.oop.travel.travelagency.dao.TourDao;
import ua.oop.travel.travelagency.dto.TourDto;
import ua.oop.travel.travelagency.mapper.TourMapper;
import ua.oop.travel.travelagency.model.Tour;

import java.sql.SQLException;
import java.util.List;

public class TourService {
    private final TourDao tourDao = new TourDao();
    private final TourMapper tourMapper = TourMapper.INSTANCE;

    // отримати всі тури (List DTO)
    public List<TourDto> getAllTours() throws SQLException {
        List<Tour> tours = tourDao.findAll();
        return tourMapper.toDtoList(tours);
    }

    // створити новий тур
    public TourDto createTour(TourDto tourDto) throws SQLException {
        // перетворюємо DTO на модель для БД
        Tour tour = tourMapper.toModel(tourDto);

        Tour savedTour = tourDao.save(tour);

        // повертаємо назад DTO з уже згенерованим ID
        return tourMapper.toDto(savedTour);
    }
}
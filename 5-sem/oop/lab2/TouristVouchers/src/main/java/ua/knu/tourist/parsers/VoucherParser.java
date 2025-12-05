package ua.knu.tourist.parsers;

import ua.knu.tourist.model.TouristVoucher;
import java.io.File;
import java.util.List;

// ->кожен парсер (DOM, SAX, StAX) зобов'язаний мати метод parse
public interface VoucherParser {
    List<TouristVoucher> parse(File file);
}
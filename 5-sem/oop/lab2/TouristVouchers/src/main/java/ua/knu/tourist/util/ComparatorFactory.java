package ua.knu.tourist.util;

import ua.knu.tourist.model.TouristVoucher;
import java.util.Comparator;

public class ComparatorFactory {

    //сортування за ціною
    public static Comparator<TouristVoucher> getCostComparator() {
        return Comparator.comparing(v -> v.getCost().getAmount());
    }

    //сортування за країною(за алфавітом)
    public static Comparator<TouristVoucher> getCountryComparator() {
        return Comparator.comparing(TouristVoucher::getCountry);
    }
}
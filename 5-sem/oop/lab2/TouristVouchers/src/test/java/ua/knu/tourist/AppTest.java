package ua.knu.tourist;

import org.junit.jupiter.api.Test;
import ua.knu.tourist.model.TouristVoucher;
import ua.knu.tourist.parsers.*;
import ua.knu.tourist.util.*;

import java.io.File;
import java.math.BigDecimal;
import java.util.List;

import static org.junit.jupiter.api.Assertions.*;

class AppTest {
    private final File xml = new File("src/test/resources/test_vouchers.xml");
    private final File xsd = new File("src/main/resources/vouchers.xsd");

    @Test
    void testValidation() {
        assertTrue(XmlValidator.validate(xsd, xml), "Test XML should be valid");
    }

    @Test
    void testAllParsersAndLogic() {
        // перевіряємо всі парсери в одному циклі
        VoucherParser[] parsers = {
                new DOMVoucherParser(),
                new SAXVoucherParser(),
                new StAXVoucherParser()
        };

        for (VoucherParser parser : parsers) {
            System.out.println("Testing parser: " + parser.getClass().getSimpleName());
            List<TouristVoucher> list = parser.parse(xml);

            // перевірка к-сті (у test_vouchers.xml має бути 2 путівки)
            assertEquals(2, list.size(), "Should parse exactly 2 vouchers");

            // перевірка сортування за ціною
            list.sort(ComparatorFactory.getCostComparator());

            TouristVoucher cheap = list.get(0);
            TouristVoucher expensive = list.get(1);

            assertEquals("TV-1111", cheap.getId());
            assertEquals(new BigDecimal("100.00"), cheap.getCost().getAmount());

            assertEquals("TV-2222", expensive.getId());
            assertEquals(new BigDecimal("500.00"), expensive.getCost().getAmount());

            // перевірка зчитування Enums
            assertEquals(TouristVoucher.VoucherType.WEEKEND, cheap.getType());
            assertEquals("TestLand", cheap.getCountry());
            assertEquals(TouristVoucher.TransportType.AUTO, cheap.getTransport());

            assertEquals(5, expensive.getHotel().getStars());
            assertTrue(expensive.getHotel().isTv());
        }
    }
}
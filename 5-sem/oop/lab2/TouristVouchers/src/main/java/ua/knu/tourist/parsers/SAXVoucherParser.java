package ua.knu.tourist.parsers;

import org.xml.sax.Attributes;
import org.xml.sax.helpers.DefaultHandler;
import ua.knu.tourist.model.TouristVoucher;

import javax.xml.parsers.SAXParser;
import javax.xml.parsers.SAXParserFactory;
import java.io.File;
import java.math.BigDecimal;
import java.util.ArrayList;
import java.util.List;

public class SAXVoucherParser implements VoucherParser {

    @Override
    public List<TouristVoucher> parse(File file) {
        try {
            SAXParserFactory factory = SAXParserFactory.newInstance();
            SAXParser saxParser = factory.newSAXParser();

            //створюємо обробник подій (Handler)
            VoucherHandler handler = new VoucherHandler();

            //запускаємо парсинг
            saxParser.parse(file, handler);

            // готовий список
            return handler.getVouchers();
        } catch (Exception e) {
            e.printStackTrace();
            return new ArrayList<>();
        }
    }

    private static class VoucherHandler extends DefaultHandler {
        private List<TouristVoucher> vouchers = new ArrayList<>();
        private TouristVoucher current;
        private StringBuilder data; // Буфер для тексту між тегами

        public List<TouristVoucher> getVouchers() {
            return vouchers;
        }

        @Override
        public void startElement(String uri, String localName, String qName, Attributes attributes) {
            // Очищаємо буфер тексту
            data = new StringBuilder();

            if (qName.equals("TouristVoucher")) {
                current = new TouristVoucher();
                current.setId(attributes.getValue("id"));
            } else if (qName.equals("Cost") && current != null) {
                current.getCost().setCurrency(attributes.getValue("currency"));
            }
        }

        @Override
        public void characters(char[] ch, int start, int length) {
            data.append(new String(ch, start, length));
        }

        @Override
        public void endElement(String uri, String localName, String qName) {
            if (current == null) return;

            String val = data.toString().trim(); // Отримуємо текст

            switch (qName) {
                case "Type": current.setType(TouristVoucher.VoucherType.valueOf(val)); break;
                case "Country": current.setCountry(val); break;
                case "Transport": current.setTransport(TouristVoucher.TransportType.valueOf(val)); break;

                // DaysNights
                case "Days": current.setDays(Integer.parseInt(val)); break;
                case "Nights": current.setNights(Integer.parseInt(val)); break;

                // Hotel
                case "Stars": current.getHotel().setStars(Integer.parseInt(val)); break;
                case "Food": current.getHotel().setFood(val); break;
                case "RoomPlaces": current.getHotel().setRoomPlaces(Integer.parseInt(val)); break;
                case "TV": current.getHotel().setTv(Boolean.parseBoolean(val)); break;
                case "AirConditioning": current.getHotel().setAirConditioning(Boolean.parseBoolean(val)); break;

                // Cost
                case "Cost": current.getCost().setAmount(new BigDecimal(val)); break;

                case "TouristVoucher":
                    vouchers.add(current);
                    current = null;
                    break;
            }
        }
    }
}
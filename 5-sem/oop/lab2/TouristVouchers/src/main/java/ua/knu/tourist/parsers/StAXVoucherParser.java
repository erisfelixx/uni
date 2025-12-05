package ua.knu.tourist.parsers;

import ua.knu.tourist.model.TouristVoucher;

import javax.xml.stream.XMLInputFactory;
import javax.xml.stream.XMLStreamConstants;
import javax.xml.stream.XMLStreamReader;
import java.io.File;
import java.io.FileInputStream;
import java.math.BigDecimal;
import java.util.ArrayList;
import java.util.List;

public class StAXVoucherParser implements VoucherParser {

    @Override
    public List<TouristVoucher> parse(File file) {
        List<TouristVoucher> vouchers = new ArrayList<>();
        TouristVoucher currentVoucher = null;
        String currentTag = "";

        try {
            XMLInputFactory factory = XMLInputFactory.newInstance();
            XMLStreamReader reader = factory.createXMLStreamReader(new FileInputStream(file));

            while (reader.hasNext()) {
                int event = reader.next();

                switch (event) {
                    case XMLStreamConstants.START_ELEMENT:
                        currentTag = reader.getLocalName();

                        if ("TouristVoucher".equals(currentTag)) {
                            currentVoucher = new TouristVoucher();
                            currentVoucher.setId(reader.getAttributeValue(null, "id"));
                        } else if ("Cost".equals(currentTag) && currentVoucher != null) {
                            currentVoucher.getCost().setCurrency(reader.getAttributeValue(null, "currency"));
                        }
                        break;

                    case XMLStreamConstants.CHARACTERS:
                        String text = reader.getText().trim();

                        if (currentVoucher != null && !text.isEmpty()) {
                            // Викликаємо метод для заповнення полів (щоб не захаращувати switch)
                            fillData(currentVoucher, currentTag, text);
                        }
                        break;

                    case XMLStreamConstants.END_ELEMENT:
                        if ("TouristVoucher".equals(reader.getLocalName())) {
                            vouchers.add(currentVoucher);
                            currentVoucher = null;
                        }
                        break;
                }
            }
        } catch (Exception e) {
            e.printStackTrace();
        }
        return vouchers;
    }

    private void fillData(TouristVoucher voucher, String tag, String text) {
        switch (tag) {
            case "Type":
                voucher.setType(TouristVoucher.VoucherType.valueOf(text));
                break;
            case "Country":
                voucher.setCountry(text);
                break;
            case "Transport":
                voucher.setTransport(TouristVoucher.TransportType.valueOf(text));
                break;
            case "Days":
                voucher.setDays(Integer.parseInt(text));
                break;
            case "Nights":
                voucher.setNights(Integer.parseInt(text));
                break;
            case "Stars":
                voucher.getHotel().setStars(Integer.parseInt(text));
                break;
            case "Food":
                voucher.getHotel().setFood(text);
                break;
            case "RoomPlaces":
                voucher.getHotel().setRoomPlaces(Integer.parseInt(text));
                break;
            case "TV":
                voucher.getHotel().setTv(Boolean.parseBoolean(text));
                break;
            case "AirConditioning":
                voucher.getHotel().setAirConditioning(Boolean.parseBoolean(text));
                break;
            case "Cost":
                voucher.getCost().setAmount(new BigDecimal(text));
                break;
        }
    }
}
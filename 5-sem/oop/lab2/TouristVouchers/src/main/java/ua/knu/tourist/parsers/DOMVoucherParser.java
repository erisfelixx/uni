package ua.knu.tourist.parsers;

import org.w3c.dom.*;
import ua.knu.tourist.model.TouristVoucher;

import javax.xml.parsers.DocumentBuilder;
import javax.xml.parsers.DocumentBuilderFactory;
import java.io.File;
import java.math.BigDecimal;
import java.util.ArrayList;
import java.util.List;

public class DOMVoucherParser implements VoucherParser {

    @Override
    public List<TouristVoucher> parse(File file) {
        List<TouristVoucher> vouchers = new ArrayList<>();
        try {
            DocumentBuilderFactory dbFactory = DocumentBuilderFactory.newInstance();
            DocumentBuilder dBuilder = dbFactory.newDocumentBuilder();

            //парсинг файлу у дерево (Document)
            Document doc = dBuilder.parse(file);
            doc.getDocumentElement().normalize();

            //отримання списку всіх вузлів <TouristVoucher>
            NodeList nList = doc.getElementsByTagName("TouristVoucher");

            for (int i = 0; i < nList.getLength(); i++) {
                Node nNode = nList.item(i);

                if (nNode.getNodeType() == Node.ELEMENT_NODE) {
                    Element element = (Element) nNode;
                    //конвертація елемента в об'єкт
                    vouchers.add(parseVoucher(element));
                }
            }
        } catch (Exception e) {
            e.printStackTrace();
        }
        return vouchers;
    }

    private TouristVoucher parseVoucher(Element el) {
        TouristVoucher v = new TouristVoucher();

        v.setId(el.getAttribute("id"));

        v.setType(TouristVoucher.VoucherType.valueOf(getTagValue(el, "Type")));
        v.setCountry(getTagValue(el, "Country"));
        v.setTransport(TouristVoucher.TransportType.valueOf(getTagValue(el, "Transport")));

        // вкладений об'єкт DaysNights
        Element dn = (Element) el.getElementsByTagName("DaysNights").item(0);
        v.setDays(Integer.parseInt(getTagValue(dn, "Days")));
        v.setNights(Integer.parseInt(getTagValue(dn, "Nights")));

        //вкладений об'єкт Hotel
        Element hotel = (Element) el.getElementsByTagName("Hotel").item(0);
        v.getHotel().setStars(Integer.parseInt(getTagValue(hotel, "Stars")));
        v.getHotel().setFood(getTagValue(hotel, "Food"));
        v.getHotel().setRoomPlaces(Integer.parseInt(getTagValue(hotel, "RoomPlaces")));
        v.getHotel().setTv(Boolean.parseBoolean(getTagValue(hotel, "TV")));
        v.getHotel().setAirConditioning(Boolean.parseBoolean(getTagValue(hotel, "AirConditioning")));
        //вкладений об'єкт Cost
        Element cost = (Element) el.getElementsByTagName("Cost").item(0);
        v.getCost().setAmount(new BigDecimal(cost.getTextContent()));
        v.getCost().setCurrency(cost.getAttribute("currency"));

        return v;
    }

    private String getTagValue(Element parent, String tag) {
        NodeList list = parent.getElementsByTagName(tag);
        if (list != null && list.getLength() > 0) {
            return list.item(0).getTextContent();
        }
        return null;
    }
}
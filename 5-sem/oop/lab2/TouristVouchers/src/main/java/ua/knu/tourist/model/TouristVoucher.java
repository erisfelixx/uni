package ua.knu.tourist.model;

import java.math.BigDecimal;
import java.util.Objects;

public class TouristVoucher implements Comparable<TouristVoucher> {

    private String id;
    private VoucherType type;
    private String country;
    private int days;
    private int nights;
    private TransportType transport;

    private Hotel hotel;
    private Cost cost;

    public TouristVoucher() {
        this.hotel = new Hotel();
        this.cost = new Cost();
    }

    // getters and setters
    public String getId() { return id; }
    public void setId(String id) { this.id = id; }

    public VoucherType getType() { return type; }
    public void setType(VoucherType type) { this.type = type; }

    public String getCountry() { return country; }
    public void setCountry(String country) { this.country = country; }

    public int getDays() { return days; }
    public void setDays(int days) { this.days = days; }

    public int getNights() { return nights; }
    public void setNights(int nights) { this.nights = nights; }

    public TransportType getTransport() { return transport; }
    public void setTransport(TransportType transport) { this.transport = transport; }

    public Hotel getHotel() { return hotel; }
    public void setHotel(Hotel hotel) { this.hotel = hotel; }

    public Cost getCost() { return cost; }
    public void setCost(Cost cost) { this.cost = cost; }



    @Override
    public String toString() {
        return String.format("Voucher [%s]: %s -> %s (%d days), Hotel: %s, Cost: %s",
                id, type, country, days, hotel, cost);
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (o == null || getClass() != o.getClass()) return false;
        TouristVoucher that = (TouristVoucher) o;
        return Objects.equals(id, that.id);
    }

    @Override
    public int hashCode() {
        return Objects.hash(id);
    }

    @Override
    public int compareTo(TouristVoucher other) {
        return this.id.compareTo(other.id);
    }

    // вкладені статичні класи для hotel +cost

    public static class Hotel {
        private int stars;
        private String food;
        private int roomPlaces;
        private boolean tv;
        private boolean airConditioning;

        public int getStars() { return stars; }
        public void setStars(int stars) { this.stars = stars; }

        public String getFood() { return food; }
        public void setFood(String food) { this.food = food; }

        public int getRoomPlaces() { return roomPlaces; }
        public void setRoomPlaces(int roomPlaces) { this.roomPlaces = roomPlaces; }

        public boolean isTv() { return tv; }
        public void setTv(boolean tv) { this.tv = tv; }

        public boolean isAirConditioning() { return airConditioning; }
        public void setAirConditioning(boolean airConditioning) { this.airConditioning = airConditioning; }

        @Override
        public String toString() {
            return stars + "* (" + food + ")";
        }
    }

    public static class Cost {
        private BigDecimal amount;
        private String currency;

        public BigDecimal getAmount() { return amount; }
        public void setAmount(BigDecimal amount) { this.amount = amount; }

        public String getCurrency() { return currency; }
        public void setCurrency(String currency) { this.currency = currency; }

        @Override
        public String toString() {
            return amount + " " + currency;
        }
    }

    public enum VoucherType {
        WEEKEND, EXCURSION, RELAXATION, PILGRIMAGE;
    }

    public enum TransportType {
        AIR, RAIL, AUTO, SHIP;
    }
}
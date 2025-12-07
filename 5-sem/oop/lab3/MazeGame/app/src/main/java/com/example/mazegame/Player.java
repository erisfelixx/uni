package com.example.mazegame;

public class Player {
    //координати гравця в лабіринті
    private int x;
    private int y;

    // задає початкову позицію при створенні гравця
    public Player(int startX, int startY) {
        this.x = startX;
        this.y = startY;
    }

    //щоб інші класи могли дізнатися, де гравець
    public int getX() {
        return x;
    }

    public int getY() {
        return y;
    }

    //для оновлення позиції (коли гравець рухається)
    public void setPosition(int newX, int newY) {
        this.x = newX;
        this.y = newY;
    }
}
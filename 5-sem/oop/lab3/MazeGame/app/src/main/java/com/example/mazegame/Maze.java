package com.example.mazegame;

import android.graphics.Point;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Random;

public class Maze {

    private int[][] map;
    private int size;

    public Maze() {
        this.size = 21; // розмір лабіринту має бути непарним
        generateMaze();
    }

    private void generateMaze() {
        map = new int[size][size];

        // заповнюємо стінами весь лабіринт
        for (int y = 0; y < size; y++) {
            for (int x = 0; x < size; x++) {
                map[y][x] = 1;
            }
        }

        // генеруємо тунелі
        carve(1, 1);

        // випадкові старт і вихід
        placeStartAndExit();
    }

    private void placeStartAndExit() {
        ArrayList<Point> floorPoints = new ArrayList<>();

        for (int y = 0; y < size; y++) {
            for (int x = 0; x < size; x++) {
                if (map[y][x] == 0) {
                    floorPoints.add(new Point(x, y));
                }
            }
        }

        if (!floorPoints.isEmpty()) {
            Random random = new Random();
            int randomIndex = random.nextInt(floorPoints.size());
            Point startPoint = floorPoints.get(randomIndex);

            map[startPoint.y][startPoint.x] = 2;

            Point bestExit = startPoint;
            double maxDistance = 0;

            for (Point p : floorPoints) {
                double distance = Math.sqrt(Math.pow(p.x - startPoint.x, 2) + Math.pow(p.y - startPoint.y, 2));

                if (distance > maxDistance) {
                    maxDistance = distance;
                    bestExit = p;
                }
            }
            map[bestExit.y][bestExit.x] = 3;
        }
    }

    // рекурсивний метод для створення шляхів
    private void carve(int x, int y) {
        map[y][x] = 0;
        ArrayList<Point> directions = new ArrayList<>();
        directions.add(new Point(0, -2));
        directions.add(new Point(0, 2));
        directions.add(new Point(-2, 0));
        directions.add(new Point(2, 0));
        Collections.shuffle(directions);

        for (Point dir : directions) {
            int newX = x + dir.x;
            int newY = y + dir.y;

            if (newX > 0 && newX < size - 1 && newY > 0 && newY < size - 1) {
                if (map[newY][newX] == 1) {
                    map[y + dir.y / 2][x + dir.x / 2] = 0;
                    carve(newX, newY);
                }
            }
        }
    }

    public int getTile(int x, int y) { return map[y][x]; }
    public int getSize() { return size; }

    public Point getStartPosition() {
        for (int y = 0; y < size; y++) {
            for (int x = 0; x < size; x++) {
                if (map[y][x] == 2) {
                    return new Point(x, y);
                }
            }
        }
        return new Point(1, 1);
    }
}
package com.example.mazegame;

import android.graphics.Point;

public class Maze {
    private int[][] map = {
            {1, 1, 1, 1, 1, 1, 1, 1, 1, 1},
            {1, 2, 0, 0, 1, 0, 0, 0, 3, 1},
            {1, 1, 1, 0, 1, 0, 1, 1, 1, 1},
            {1, 0, 0, 0, 1, 0, 0, 0, 0, 1},
            {1, 0, 1, 1, 1, 1, 1, 1, 0, 1},
            {1, 0, 0, 0, 0, 0, 0, 0, 0, 1},
            {1, 1, 1, 1, 1, 0, 1, 1, 1, 1},
            {1, 0, 0, 1, 0, 0, 0, 0, 0, 1},
            {1, 1, 0, 0, 0, 1, 1, 1, 0, 1},
            {1, 1, 1, 1, 1, 1, 1, 1, 1, 1}
    };

    //щоб дізнатися, що знаходиться в конкретній клітинці
    public int getTile(int x, int y) {
        return map[y][x]; // Увага: в масивах спочатку йде Рядок (Y), потім Стовпець (X)
    }
    public int getSize() {
        return map.length;
    }

    // стартова позиція
    public Point getStartPosition() {
        for (int row = 0; row < map.length; row++) {
            for (int col = 0; col < map[0].length; col++) {
                if (map[row][col] == 2) {
                    return new Point(col, row);
                }
            }
        }
        return new Point(1, 1);
    }
}
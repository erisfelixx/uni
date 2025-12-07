package com.example.mazegame;

import android.content.Context;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.view.View;

public class GameView extends View {

    private Maze maze;
    private Player player;

    private Paint wallPaint;
    private Paint playerPaint;
    private Paint exitPaint;
    private Paint pathPaint;

    private float cellSize;

    // конструктор
    public GameView(Context context) {
        super(context);

        maze = new Maze();
        // гравець на стартовій позиції
        player = new Player(maze.getStartPosition().x, maze.getStartPosition().y);

        wallPaint = new Paint();
        wallPaint.setColor(Color.BLACK);

        playerPaint = new Paint();
        playerPaint.setColor(Color.RED);

        exitPaint = new Paint();
        exitPaint.setColor(Color.GREEN);

        pathPaint = new Paint();
        pathPaint.setColor(Color.LTGRAY);
    }

    // головний метод малювання
    @Override
    protected void onDraw(Canvas canvas) {
        super.onDraw(canvas);

        int width = getWidth();
        int height = getHeight();

        // розмір клітинки = ширина екрану/кількість клітинок у рядку
        cellSize = width / (float) maze.getSize();

        for (int y = 0; y < maze.getSize(); y++) {
            for (int x = 0; x < maze.getSize(); x++) {

                float left = x * cellSize;
                float top = y * cellSize;
                float right = left + cellSize;
                float bottom = top + cellSize;

                int tileType = maze.getTile(x, y);

                if (tileType == 1) {
                    //малюємо стіну (квадрат)
                    canvas.drawRect(left, top, right, bottom, wallPaint);
                } else if (tileType == 3) {
                    //малюємо вихід
                    canvas.drawRect(left, top, right, bottom, exitPaint);
                } else {
                    //малюємо підлогу (прохід)
                    canvas.drawRect(left, top, right, bottom, pathPaint);
                }
            }
        }

        // гравець
        float playerCenterX = player.getX() * cellSize + cellSize / 2;
        float playerCenterY = player.getY() * cellSize + cellSize / 2;
        float playerRadius = cellSize / 2.5f;

        canvas.drawCircle(playerCenterX, playerCenterY, playerRadius, playerPaint);
    }

    // логіка руху
    public void movePlayer(int dx, int dy) {
        // 1. Рахуємо, куди гравець ХОЧЕ піти
        int newX = player.getX() + dx;
        int newY = player.getY() + dy;

        // перевірка на вихід за межі масиву (щоб програма не вилетіла)
        if (newX >= 0 && newX < maze.getSize() && newY >= 0 && newY < maze.getSize()) {

            // перевірка на стіну
            if (maze.getTile(newX, newY) != 1) {
                player.setPosition(newX, newY);

                invalidate();

                checkWin();
            }
        }
    }

    private void checkWin() {
        if (maze.getTile(player.getX(), player.getY()) == 3) {  //вихід!
            playerPaint.setColor(Color.GREEN);
        }
    }
}
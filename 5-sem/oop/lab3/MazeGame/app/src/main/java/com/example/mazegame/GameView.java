package com.example.mazegame;

import android.content.Context;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.graphics.RectF;
import android.view.View;

public class GameView extends View {
    private Maze maze;
    private Player player;

    private Paint wallPaint;
    private Paint playerPaint;
    private Paint exitPaint;
    private Paint pathPaint;
    private Paint gridPaint;
    private Paint glowPaint;

    private float cellSize;

    private int stepCount = 0;
    private long startTime;
    private boolean gameWon = false;

    // конструктор
    public GameView(Context context) {
        super(context);

        maze = new Maze();
        // гравець на стартовій позиції
        player = new Player(maze.getStartPosition().x, maze.getStartPosition().y);

        wallPaint = new Paint();
        wallPaint.setColor(Color.BLACK);
        wallPaint.setStyle(Paint.Style.FILL);
        wallPaint.setAntiAlias(true);

        playerPaint = new Paint();
        playerPaint.setColor(Color.parseColor("#E74C3C"));
        playerPaint.setStyle(Paint.Style.FILL);
        playerPaint.setAntiAlias(true);

        exitPaint = new Paint();
        exitPaint.setColor(Color.parseColor("#27AE60"));
        exitPaint.setStyle(Paint.Style.FILL);
        exitPaint.setAntiAlias(true);

        pathPaint = new Paint();
        pathPaint.setColor(Color.parseColor("#ECF0F1"));
        pathPaint.setStyle(Paint.Style.FILL);
        pathPaint.setAntiAlias(true);

        gridPaint = new Paint();
        gridPaint.setColor(Color.parseColor("#BDC3C7"));
        gridPaint.setStyle(Paint.Style.STROKE);
        gridPaint.setStrokeWidth(1f);
        gridPaint.setAntiAlias(true);

        glowPaint = new Paint();
        glowPaint.setColor(Color.parseColor("#E74C3C"));
        glowPaint.setAlpha(80);
        glowPaint.setStyle(Paint.Style.FILL);
        glowPaint.setAntiAlias(true);

        // запускаємо таймер
        startTime = System.currentTimeMillis();
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
                    canvas.drawRect(left, top, right, bottom, wallPaint);
                } else if (tileType == 3) {
                    canvas.drawRect(left, top, right, bottom, exitPaint);

                    Paint exitGlowPaint = new Paint();
                    exitGlowPaint.setColor(Color.parseColor("#27AE60"));
                    exitGlowPaint.setAlpha(60);
                    exitGlowPaint.setStyle(Paint.Style.FILL);
                    exitGlowPaint.setAntiAlias(true);
                    canvas.drawRect(left - 4, top - 4, right + 4, bottom + 4, exitGlowPaint);
                } else {
                    canvas.drawRect(left, top, right, bottom, pathPaint);
                }
            }
        }

        // гравець
        float playerCenterX = player.getX() * cellSize + cellSize / 2;
        float playerCenterY = player.getY() * cellSize + cellSize / 2;
        float playerRadius = cellSize / 3f;

        canvas.drawCircle(playerCenterX, playerCenterY, playerRadius * 1.5f, glowPaint);

        canvas.drawCircle(playerCenterX, playerCenterY, playerRadius, playerPaint);
        Paint centerPaint = new Paint();
        centerPaint.setColor(Color.WHITE);
        centerPaint.setStyle(Paint.Style.FILL);
        centerPaint.setAntiAlias(true);
        canvas.drawCircle(playerCenterX, playerCenterY, playerRadius * 0.4f, centerPaint);

        drawStats(canvas);
    }

    private void drawStats(Canvas canvas) {
        Paint textPaint = new Paint();
        textPaint.setColor(Color.BLACK);
        textPaint.setTextSize(40);
        textPaint.setAntiAlias(true);
        textPaint.setStyle(Paint.Style.FILL);

        // лічильник кроків
        canvas.drawText("Кроки: " + stepCount, 20, 50, textPaint);

        // таймер
        if (!gameWon) {
            long elapsedTime = (System.currentTimeMillis() - startTime) / 1000;
            canvas.drawText("Час: " + elapsedTime + "с", 20, 100, textPaint);
            invalidate(); // оновлюємо для таймера
        } else {
            long finalTime = (System.currentTimeMillis() - startTime) / 1000;
            canvas.drawText("Час: " + finalTime + "с", 20, 100, textPaint);
        }
    }

    private void checkWin() {
        if (maze.getTile(player.getX(), player.getY()) == 3) {  // вихід!
            gameWon = true;
            // змінюємо колір гравця на зелений при перемозі
            playerPaint.setColor(Color.parseColor("#27AE60"));
            glowPaint.setColor(Color.parseColor("#27AE60"));
        }
    }

    // метод для створення нового лабіринту
    public void generateNewMaze() {
        maze = new Maze();
        player = new Player(maze.getStartPosition().x, maze.getStartPosition().y);

        // скидаємо статистику
        stepCount = 0;
        startTime = System.currentTimeMillis();
        gameWon = false;

        // повертаємо колір гравця на червоний
        playerPaint.setColor(Color.parseColor("#E74C3C"));
        glowPaint.setColor(Color.parseColor("#E74C3C"));
        glowPaint.setAlpha(80);

        invalidate();
    }
}
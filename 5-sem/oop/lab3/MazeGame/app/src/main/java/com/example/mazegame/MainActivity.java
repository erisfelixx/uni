package com.example.mazegame;

import android.os.Bundle;
import android.os.Handler;
import android.widget.Button;
import android.widget.FrameLayout;
import android.widget.TextView;

import androidx.appcompat.app.AppCompatActivity;

public class MainActivity extends AppCompatActivity {

    private GameView gameView;
    private TextView tvSteps;
    private TextView tvTime;
    private Handler handler = new Handler();
    private Runnable updateStatsRunnable;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        //знаходимо контейнер на екрані
        FrameLayout container = findViewById(R.id.game_container);

        // створюємо гру (GameView) +додаємо її в контейнер
        gameView = new GameView(this);
        container.addView(gameView);

        // знаходимо TextView для статистики
        tvSteps = findViewById(R.id.tv_steps);
        tvTime = findViewById(R.id.tv_time);

        // кнопки руху
        Button btnUp = findViewById(R.id.btn_up);
        Button btnDown = findViewById(R.id.btn_down);
        Button btnLeft = findViewById(R.id.btn_left);
        Button btnRight = findViewById(R.id.btn_right);

        btnUp.setOnClickListener(v -> {
            gameView.movePlayer(0, -1);
            updateStats();
        });
        btnDown.setOnClickListener(v -> {
            gameView.movePlayer(0, 1);
            updateStats();
        });
        btnLeft.setOnClickListener(v -> {
            gameView.movePlayer(-1, 0);
            updateStats();
        });
        btnRight.setOnClickListener(v -> {
            gameView.movePlayer(1, 0);
            updateStats();
        });

        // кнопка нового лабіринту
        Button btnNewMaze = findViewById(R.id.btn_new_maze);
        btnNewMaze.setOnClickListener(v -> {
            gameView.generateNewMaze();
            updateStats();
        });

        // Запускаємо оновлення таймера
        startStatsUpdate();
    }

    private void startStatsUpdate() {
        updateStatsRunnable = new Runnable() {
            @Override
            public void run() {
                updateStats();
                handler.postDelayed(this, 100); // оновлюємо кожні 100мс
            }
        };
        handler.post(updateStatsRunnable);
    }

    private void updateStats() {
        tvSteps.setText("Кроки: " + gameView.getStepCount());
        tvTime.setText("Час: " + gameView.getElapsedTime() + "с");
    }

    @Override
    protected void onDestroy() {
        super.onDestroy();
        handler.removeCallbacks(updateStatsRunnable);
    }
}
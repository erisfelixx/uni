package com.example.mazegame;

import android.os.Bundle;
import android.widget.Button;
import android.widget.FrameLayout;

import androidx.appcompat.app.AppCompatActivity;

public class MainActivity extends AppCompatActivity {

    private GameView gameView;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        //знаходимо контейнер на екрані
        FrameLayout container = findViewById(R.id.game_container);

        // створюємо гру (GameView) +додаємо її в контейнер
        gameView = new GameView(this);
        container.addView(gameView);

        // кнопки
        Button btnUp = findViewById(R.id.btn_up);
        Button btnDown = findViewById(R.id.btn_down);
        Button btnLeft = findViewById(R.id.btn_left);
        Button btnRight = findViewById(R.id.btn_right);

        // вгору, вниз, вліво, вправо
        btnUp.setOnClickListener(v -> gameView.movePlayer(0, -1));
        btnDown.setOnClickListener(v -> gameView.movePlayer(0, 1));
        btnLeft.setOnClickListener(v -> gameView.movePlayer(-1, 0));
        btnRight.setOnClickListener(v -> gameView.movePlayer(1, 0));
    }
}
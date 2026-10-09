import sys
from PySide6.QtCore import Qt, QUrl
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtWidgets import (
    QApplication, QFileDialog, QHBoxLayout, QLabel,
    QPushButton, QSlider, QVBoxLayout, QWidget,
)

SEEK_STEP_MS = 10_000  # крок перемотки: 10 секунд

def format_time(ms):
    """Перетворює мілісекунди у рядок мм:сс."""
    total_seconds = ms // 1000
    minutes, seconds = divmod(total_seconds, 60)
    return f"{minutes:02d}:{seconds:02d}"


class MediaPlayer(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Медіаплеєр")
        self.resize(640, 480)

        # Рушій відтворення, вихід звуку, екран для відео
        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.video_widget = QVideoWidget()
        self.player.setAudioOutput(self.audio_output)
        self.player.setVideoOutput(self.video_widget)
        self.audio_output.setVolume(0.7)

        # Кнопки
        self.open_btn = QPushButton("Відкрити файл")
        self.back_btn = QPushButton("-10 с")
        self.play_btn = QPushButton("Play / Pause")
        self.stop_btn = QPushButton("Stop")
        self.forward_btn = QPushButton("+10 с")

        # Прогрес-бар і мітки часу
        self.position_slider = QSlider(Qt.Horizontal)
        self.current_label = QLabel("00:00")
        self.total_label = QLabel("00:00")

        # Повзунок гучності
        self.volume_label = QLabel("Гучність")
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(70)
        self.volume_slider.setFixedWidth(120)

        # Сигнали -> слоти
        self.open_btn.clicked.connect(self.open_file)
        self.back_btn.clicked.connect(self.seek_back)
        self.play_btn.clicked.connect(self.toggle_play)
        self.stop_btn.clicked.connect(self.player.stop)
        self.forward_btn.clicked.connect(self.seek_forward)

        self.player.positionChanged.connect(self.on_position_changed)
        self.player.durationChanged.connect(self.on_duration_changed)
        self.position_slider.sliderMoved.connect(self.player.setPosition)
        self.volume_slider.valueChanged.connect(self.on_volume_changed)

        # Розташування
        progress_row = QHBoxLayout()
        progress_row.addWidget(self.current_label)
        progress_row.addWidget(self.position_slider)
        progress_row.addWidget(self.total_label)

        buttons_row = QHBoxLayout()
        buttons_row.addWidget(self.open_btn)
        buttons_row.addWidget(self.back_btn)
        buttons_row.addWidget(self.play_btn)
        buttons_row.addWidget(self.stop_btn)
        buttons_row.addWidget(self.forward_btn)
        buttons_row.addStretch()
        buttons_row.addWidget(self.volume_label)
        buttons_row.addWidget(self.volume_slider)

        layout = QVBoxLayout(self)
        layout.addWidget(self.video_widget)
        layout.addLayout(progress_row)
        layout.addLayout(buttons_row)

    def open_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Обрати медіафайл", "",
            "Медіа (*.mp3 *.wav *.mp4 *.mov);;Усі файли (*)",
        )
        if path:
            self.player.setSource(QUrl.fromLocalFile(path))
            self.player.play()

    def toggle_play(self):
        if self.player.playbackState() == QMediaPlayer.PlayingState:
            self.player.pause()
        else:
            self.player.play()

    def seek_back(self):
        self.player.setPosition(max(0, self.player.position() - SEEK_STEP_MS))

    def seek_forward(self):
        new_pos = self.player.position() + SEEK_STEP_MS
        self.player.setPosition(min(self.player.duration(), new_pos))

    def on_position_changed(self, position):
        self.position_slider.setValue(position)
        self.current_label.setText(format_time(position))

    def on_duration_changed(self, duration):
        self.position_slider.setRange(0, duration)
        self.total_label.setText(format_time(duration))

    def on_volume_changed(self, value):
        self.audio_output.setVolume(value / 100)


app = QApplication(sys.argv)
window = MediaPlayer()
window.show()
sys.exit(app.exec())
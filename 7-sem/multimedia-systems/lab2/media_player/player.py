import sys
from PySide6.QtCore import QUrl
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtWidgets import (
    QApplication, QFileDialog, QHBoxLayout,
    QPushButton, QVBoxLayout, QWidget,
)


class MediaPlayer(QWidget)
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Медіаплеєр")
        self.resize(640, 480)

        # Рушій відтворення + вихід звуку + екран для відео
        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.video_widget = QVideoWidget()
        self.player.setAudioOutput(self.audio_output)
        self.player.setVideoOutput(self.video_widget)

        # Кнопки
        self.open_btn = QPushButton("Відкрити файл")
        self.play_btn = QPushButton("Play / Pause")
        self.stop_btn = QPushButton("Stop")

        # Підключаємо кнопки до дій (сигнал -> слот)
        self.open_btn.clicked.connect(self.open_file)
        self.play_btn.clicked.connect(self.toggle_play)
        self.stop_btn.clicked.connect(self.player.stop)

        # Розташування елементів у вікні
        buttons = QHBoxLayout()
        buttons.addWidget(self.open_btn)
        buttons.addWidget(self.play_btn)
        buttons.addWidget(self.stop_btn)

        layout = QVBoxLayout(self)
        layout.addWidget(self.video_widget)
        layout.addLayout(buttons)

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


app = QApplication(sys.argv)
window = MediaPlayer()
window.show()
sys.exit(app.exec())
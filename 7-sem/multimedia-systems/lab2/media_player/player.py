import sys
from pathlib import Path
from PySide6.QtCore import Qt, QSettings, QSize, QUrl
from PySide6.QtGui import QPainter, QPixmap
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtWidgets import (
    QApplication, QFileDialog, QFrame, QHBoxLayout, QLabel, QLineEdit,
    QListWidget, QListWidgetItem, QMessageBox, QPushButton, QSizePolicy,
    QSlider, QVBoxLayout, QWidget,
)
from theme import ASSETS_DIR, STYLE, icon, load_pixel_font

SEEK_STEP_MS = 10_000  # крок перемотки: 10 секунд
RECENT_LIMIT = 10  # скільки останніх файлів пам'ятаємо


def format_time(ms):
    """Перетворює мілісекунди у рядок мм:сс."""
    total_seconds = ms // 1000
    minutes, seconds = divmod(total_seconds, 60)
    return f"{minutes:02d}:{seconds:02d}"


def is_url(source):
    """True, якщо джерело — посилання, а не шлях до локального файлу."""
    return source.startswith(("http://", "https://"))


def source_title(source):
    """Назва для показу: у файлу — ім'я без шляху, у посилання — воно саме."""
    return source if is_url(source) else source.replace("\\", "/").split("/")[-1]


class MediaPlayer(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Медіаплеєр")
        self.resize(980, 620)
        self.setStyleSheet(STYLE)

        # Піксельний фон вікна (малюється у paintEvent)
        self.bg_pixmap = QPixmap(str(ASSETS_DIR / "bg.png"))

        # Рушій відтворення, вихід звуку, екран для відео
        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.video_widget = QVideoWidget()
        self.player.setAudioOutput(self.audio_output)
        self.player.setVideoOutput(self.video_widget)
        self.audio_output.setVolume(0.7)

        # Кнопки (тепер із піксельними іконками замість тексту)
        self.open_btn = QPushButton(" Відкрити файл")
        self.open_btn.setIcon(icon("folder"))
        self.back_btn = QPushButton()
        self.back_btn.setIcon(icon("back"))
        self.back_btn.setToolTip("-10 с")
        self.play_btn = QPushButton()
        self.play_btn.setIcon(icon("play"))
        self.play_btn.setIconSize(QSize(32, 32))
        self.stop_btn = QPushButton()
        self.stop_btn.setIcon(icon("stop"))
        self.stop_btn.setToolTip("Stop")
        self.forward_btn = QPushButton()
        self.forward_btn.setIcon(icon("forward"))
        self.forward_btn.setToolTip("+10 с")

        # Імена для QSS: велика кругла Play і круглі бічні кнопки
        self.play_btn.setObjectName("bigplay")
        for btn in (self.back_btn, self.stop_btn, self.forward_btn):
            btn.setObjectName("round")
            btn.setIconSize(QSize(24, 24))

        # Прогрес-бар і мітки часу
        self.position_slider = QSlider(Qt.Horizontal)
        self.current_label = QLabel("00:00")
        self.total_label = QLabel("00:00")

        # Назва поточного файлу
        self.title_label = QLabel("Не вибрано файл")
        self.title_label.setObjectName("title")
        self.title_label.setAlignment(Qt.AlignCenter)
        # Ignored: довга назва/посилання обрізається, а не розтягує вікно
        self.title_label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)

        # Плашка "Зараз відтворюється"
        self.pill_label = QLabel("Зараз відтворюється")
        self.pill_label.setObjectName("pill")

        # Повзунок гучності (іконка динаміка замість тексту)
        self.volume_label = QLabel()
        self.volume_label.setPixmap(
            QPixmap(str(ASSETS_DIR / "icons" / "volume.png")).scaled(
                28, 28, Qt.KeepAspectRatio, Qt.FastTransformation
            )
        )
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setObjectName("volume")
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(70)
        self.volume_slider.setFixedWidth(160)

        # Поле для посилання та кнопка
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText(
            "Вставте пряме посилання на медіафайл (.mp4, .mp3 ...)"
        )
        self.url_btn = QPushButton(" Відтворити за URL")
        self.url_btn.setIcon(icon("link"))

        # Сигнали -> слоти
        self.open_btn.clicked.connect(self.open_file)
        self.back_btn.clicked.connect(self.seek_back)
        self.play_btn.clicked.connect(self.toggle_play)
        self.stop_btn.clicked.connect(self.player.stop)
        self.forward_btn.clicked.connect(self.seek_forward)
        self.url_btn.clicked.connect(self.open_url)
        self.url_input.returnPressed.connect(self.open_url)

        self.player.positionChanged.connect(self.on_position_changed)
        self.player.durationChanged.connect(self.on_duration_changed)
        self.player.playbackStateChanged.connect(self.on_state_changed)
        self.player.errorOccurred.connect(self.on_error)
        self.position_slider.sliderMoved.connect(self.player.setPosition)
        self.volume_slider.valueChanged.connect(self.on_volume_changed)

        # Розташування
        # Екран для відео в рамці (рамка — з QSS, відео розтягується по рамці)
        screen_frame = QFrame()
        screen_frame.setObjectName("screen")
        screen_layout = QVBoxLayout(screen_frame)
        screen_layout.setContentsMargins(3, 3, 3, 3)
        screen_layout.addWidget(self.video_widget)

        pill_row = QHBoxLayout()
        pill_row.addWidget(self.pill_label)
        pill_row.addStretch()

        url_row = QHBoxLayout()
        url_row.addWidget(self.url_input)
        url_row.addWidget(self.url_btn)

        progress_row = QHBoxLayout()
        progress_row.addWidget(self.current_label)
        progress_row.addWidget(self.position_slider)
        progress_row.addWidget(self.total_label)

        # Кнопки керування по центру: назад, Play/Pause, Stop, вперед
        buttons_row = QHBoxLayout()
        buttons_row.addStretch()
        buttons_row.addWidget(self.back_btn)
        buttons_row.addWidget(self.play_btn)
        buttons_row.addWidget(self.stop_btn)
        buttons_row.addWidget(self.forward_btn)
        buttons_row.addStretch()

        # Нижній рядок: відкрити файл і гучність
        bottom_row = QHBoxLayout()
        bottom_row.addWidget(self.open_btn)
        bottom_row.addStretch()
        bottom_row.addWidget(self.volume_label)
        bottom_row.addWidget(self.volume_slider)

        # Ліва картка — сам плеєр
        player_card = QFrame()
        player_card.setObjectName("card")
        card_layout = QVBoxLayout(player_card)
        card_layout.setContentsMargins(16, 14, 16, 14)
        card_layout.setSpacing(10)
        card_layout.addLayout(pill_row)
        card_layout.addWidget(screen_frame, 1)  # 1 = забирає весь вільний простір
        card_layout.addWidget(self.title_label)
        card_layout.addLayout(progress_row)
        card_layout.addLayout(buttons_row)
        card_layout.addLayout(url_row)
        card_layout.addLayout(bottom_row)

        # Права картка "Останнє переглянуте": список файлів, що зберігається між запусками
        self.settings = QSettings("lab2", "MediaPlayer")  # сховище налаштувань ОС
        recent_icon = QLabel()
        recent_icon.setPixmap(
            QPixmap(str(ASSETS_DIR / "icons" / "recent.png")).scaled(
                28, 28, Qt.KeepAspectRatio, Qt.FastTransformation
            )
        )
        recent_title = QLabel("Останнє переглянуте")
        recent_title.setObjectName("card_title")
        recent_header = QHBoxLayout()
        recent_header.addWidget(recent_icon)
        recent_header.addWidget(recent_title)
        recent_header.addStretch()

        # Список (клік по елементу — відтворити) і напис для порожнього стану
        self.recent_list = QListWidget()
        self.recent_list.setObjectName("recent")
        self.recent_list.setIconSize(QSize(32, 32))
        self.recent_list.itemClicked.connect(self.play_recent)

        self.recent_empty = QLabel("Тут з'являтимуться\nостанні файли")
        self.recent_empty.setObjectName("empty")
        self.recent_empty.setAlignment(Qt.AlignCenter)

        recent_card = QFrame()
        recent_card.setObjectName("card")
        recent_card.setFixedWidth(250)
        recent_layout = QVBoxLayout(recent_card)
        recent_layout.setContentsMargins(16, 14, 16, 14)
        recent_layout.addLayout(recent_header)
        recent_layout.addWidget(self.recent_list, 1)
        recent_layout.addWidget(self.recent_empty, 1)

        # Логотип зверху
        logo = QLabel()
        logo.setPixmap(
            QPixmap(str(ASSETS_DIR / "icons" / "bunny.png")).scaled(
                44, 44, Qt.KeepAspectRatio, Qt.FastTransformation
            )
        )
        brand = QLabel("Медіаплеєр")
        brand.setObjectName("brand")
        brand_row = QHBoxLayout()
        brand_row.addWidget(logo)
        brand_row.addWidget(brand)
        brand_row.addStretch()

        body = QHBoxLayout()
        body.setSpacing(16)
        body.addWidget(player_card, 1)
        body.addWidget(recent_card)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 14, 20, 20)
        layout.addLayout(brand_row)
        layout.addLayout(body, 1)

        self.refresh_recent()  # показуємо збережений список одразу після запуску

    def paintEvent(self, event):
        """Малює піксельний фон на все вікно (із збереженням пропорцій)."""
        painter = QPainter(self)
        if self.bg_pixmap.isNull():
            painter.fillRect(self.rect(), Qt.white)
            return
        scaled = self.bg_pixmap.scaled(
            self.size(), Qt.KeepAspectRatioByExpanding, Qt.FastTransformation
        )
        x = (self.width() - scaled.width()) // 2
        y = (self.height() - scaled.height()) // 2
        painter.drawPixmap(x, y, scaled)

    def open_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Обрати медіафайл", "",
            "Медіа (*.mp3 *.wav *.mp4 *.mov);;Усі файли (*)",
        )
        if path:
            self.play_source(path)

    def open_url(self):
        text = self.url_input.text().strip()
        if text:
            self.play_source(text)

    def play_source(self, source):
        """Запускає файл або посилання й запам'ятовує його у 'Останньому переглянутому'."""
        self.title_label.setText(source_title(source))
        if is_url(source):
            self.player.setSource(QUrl(source))
        else:
            self.player.setSource(QUrl.fromLocalFile(source))
        self.player.play()
        self.add_recent(source)

    def get_recent(self):
        """Читає список останніх джерел зі сховища налаштувань."""
        items = self.settings.value("recent", [])
        if isinstance(items, str):  # якщо у списку один елемент, Qt повертає рядок
            items = [items]
        return list(items) if items else []

    def add_recent(self, source):
        """Ставить джерело на початок списку без дублікатів, обрізає до ліміту."""
        items = [s for s in self.get_recent() if s != source]
        items.insert(0, source)
        self.settings.setValue("recent", items[:RECENT_LIMIT])
        self.refresh_recent()

    def refresh_recent(self):
        """Перемальовує список; якщо він порожній — показує напис-заглушку."""
        items = self.get_recent()
        self.recent_list.clear()
        for source in items:
            item = QListWidgetItem(icon("heart"), source_title(source))
            item.setData(Qt.UserRole, source)  # справжній шлях/посилання
            item.setToolTip(source)
            self.recent_list.addItem(item)
        self.recent_list.setVisible(bool(items))
        self.recent_empty.setVisible(not items)

    def play_recent(self, item):
        source = item.data(Qt.UserRole)
        # Локальний файл могли видалити чи перемістити — тоді прибираємо його зі списку
        if not is_url(source) and not Path(source).exists():
            QMessageBox.warning(self, "Файл не знайдено", source)
            self.settings.setValue(
                "recent", [s for s in self.get_recent() if s != source]
            )
            self.refresh_recent()
            return
        self.play_source(source)

    def toggle_play(self):
        if self.player.playbackState() == QMediaPlayer.PlayingState:
            self.player.pause()
        else:
            self.player.play()

    def on_state_changed(self, state):
        # Замість тексту Play/Pause міняємо іконку на кнопці
        is_playing = state == QMediaPlayer.PlayingState
        self.play_btn.setIcon(icon("pause" if is_playing else "play"))

    def seek_back(self):
        self.player.setPosition(max(0, self.player.position() - SEEK_STEP_MS))

    def seek_forward(self):
        new_pos = self.player.position() + SEEK_STEP_MS
        self.player.setPosition(min(self.player.duration(), new_pos))

    def on_position_changed(self, position):
        if not self.position_slider.isSliderDown():
            self.position_slider.setValue(position)
        self.current_label.setText(format_time(position))

    def on_duration_changed(self, duration):
        self.position_slider.setRange(0, duration)
        self.total_label.setText(format_time(duration))

    def on_volume_changed(self, value):
        self.audio_output.setVolume(value / 100)

    def on_error(self, error, error_string):
        QMessageBox.warning(self, "Помилка відтворення", error_string)


app = QApplication(sys.argv)
load_pixel_font()  # шрифт підключаємо після створення QApplication
window = MediaPlayer()
window.show()
sys.exit(app.exec())
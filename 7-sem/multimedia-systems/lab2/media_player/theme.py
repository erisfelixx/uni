"""Оформлення плеєра: шляхи до ресурсів, стилі (QSS), іконки, шрифт.
Тут лише дизайн — логіка відтворення живе в player.py."""
from pathlib import Path
from PySide6.QtGui import QFont, QFontDatabase, QIcon
from PySide6.QtWidgets import QApplication

# Шляхи до ресурсів дизайну (відносно цього файлу, щоб працювало з будь-якої папки)
BASE_DIR = Path(__file__).resolve().parent
ASSETS_DIR = BASE_DIR / "assets"
FONTS_DIR = BASE_DIR / "fonts"

# Таблиця стилів (QSS) — це "CSS для Qt". @ASSETS@ підміняється на справжній шлях.
STYLE = """
QLabel { color: #5A3E8E; }

QLabel#brand { font-size: 22px; color: #7B5CB8; }
QLabel#pill {
    background: #F0A6D8; color: #FFFFFF;
    border: 2px solid #E26AA0; border-radius: 10px;
    padding: 2px 12px;
}
QLabel#title { font-size: 20px; color: #4B3B7A; }
QLabel#card_title { font-size: 18px; color: #4B3B7A; }
QLabel#empty { color: #9A86C2; }

QFrame#card {
    background: #F6E9F8;
    border: 3px solid #D3B3EE;
    border-radius: 8px;
}
QFrame#screen {
    background: #1E1530;
    border: 3px solid #A992D6;
    border-radius: 6px;
}

QPushButton {
    background: #EBD9F7; color: #5A3E8E;
    border: 2px solid #A992D6; border-radius: 8px;
    padding: 6px 12px;
}
QPushButton:hover { background: #F5E8FB; }
QPushButton:pressed { background: #D9BFF0; }

QPushButton#round {
    border-radius: 24px; min-width: 48px; max-width: 48px;
    min-height: 48px; max-height: 48px; padding: 0;
}
QPushButton#bigplay {
    background: #B58BE0; border: 3px solid #7B5CB8; border-radius: 36px;
    min-width: 72px; max-width: 72px; min-height: 72px; max-height: 72px;
    padding: 0;
}
QPushButton#bigplay:hover { background: #C49CEA; }
QPushButton#bigplay:pressed { background: #9F73CF; }

QLineEdit {
    background: #FFFFFF; color: #4B3B7A;
    border: 2px solid #D3B3EE; border-radius: 8px;
    padding: 6px 10px; selection-background-color: #F0A6D8;
}
QLineEdit:focus { border-color: #B58BE0; }

QSlider::groove:horizontal {
    height: 8px; background: #E3D2F3;
    border: 2px solid #C9A8EA; border-radius: 6px;
}
QSlider::sub-page:horizontal {
    background: #B58BE0; border: 2px solid #B58BE0; border-radius: 6px;
}
QSlider::handle:horizontal {
    image: url("@ASSETS@/icons/star.png");
    width: 32px; height: 32px; margin: -14px 0;
    background: transparent; border: none;
}

QSlider#volume::sub-page:horizontal {
    background: #F28BB0; border: 2px solid #F28BB0; border-radius: 6px;
}
QSlider#volume::handle:horizontal {
    image: url("@ASSETS@/icons/heart.png");
    width: 32px; height: 32px; margin: -14px 0;
    background: transparent; border: none;
}
""".replace("@ASSETS@", ASSETS_DIR.as_posix())


def icon(name):
    """Завантажує піксельну іконку з assets/icons/<name>.png."""
    return QIcon(str(ASSETS_DIR / "icons" / f"{name}.png"))


def load_pixel_font():
    """Підключає піксельний шрифт із папки fonts/. Якщо файлу немає — лишається системний."""
    for path in sorted(FONTS_DIR.glob("*.ttf")):
        font_id = QFontDatabase.addApplicationFont(str(path))
        if font_id != -1:
            families = QFontDatabase.applicationFontFamilies(font_id)
            if families:
                QApplication.setFont(QFont(families[0], 13))
                return
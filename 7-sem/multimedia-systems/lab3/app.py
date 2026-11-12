import sys
from pathlib import Path

import numpy as np
from PIL import Image
from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import (
    QApplication, QDialog, QFileDialog, QFrame, QHBoxLayout, QLabel,
    QMessageBox, QPushButton, QSlider, QSpinBox, QTextEdit, QVBoxLayout,
    QWidget,
)

BLOCK = 8            # розмір блока для DCT
IMAGE_SIZE = 512     # сторона робочого зображення (кратна 8 і степеню 2)
PANEL_SIZE = 340     # розмір панелі показу на екрані
DEFAULT_LEVELS = 3   # кількість рівнів розкладу Хаара за замовчуванням
EXPERIMENT_RATIOS = (0.50, 0.25, 0.10, 0.05, 0.01)  # рівні для експериментів


# DCT (блоки 8x8)
def dct_matrix(n=BLOCK):
    """
    Матриця прямого DCT-II: C[k, m] = a(k) * cos((2m+1) * k * pi / 2n).
    Матриця ортонормована (C * C^T = I), тому матриця оберненого перетворення — це просто C^T, окремо її рахувати не потрібно
    """
    k = np.arange(n).reshape(-1, 1)   # номер частоти — рядок матриці
    m = np.arange(n).reshape(1, -1)   # номер відліку — стовпець матриці
    basis = np.cos((2 * m + 1) * k * np.pi / (2 * n))
    alpha = np.full((n, 1), np.sqrt(2.0 / n))
    alpha[0, 0] = np.sqrt(1.0 / n)    # нульова частота має інший множник
    return alpha * basis


def split_blocks(img, n=BLOCK):
    """Розрізає зображення на блоки: (H, W) -> (H/n, W/n, n, n)."""
    h, w = img.shape
    return img.reshape(h // n, n, w // n, n).swapaxes(1, 2)


def merge_blocks(blocks):
    """Збирає зображення назад із блоків."""
    nby, nbx, n, _ = blocks.shape
    return blocks.swapaxes(1, 2).reshape(nby * n, nbx * n)


def dct2_blocks(img, c):
    """Пряме DCT: для кожного блока B рахуємо F = C * B * C^T.

    einsum виконує це множення одразу для всіх блоків зображення.
    Зсув на 128 центрує яскравість навколо нуля (як у стандарті JPEG)
    """
    blocks = split_blocks(img) - 128.0
    return np.einsum("ij,abjk,lk->abil", c, blocks, c)


def idct2_blocks(coeffs, c):
    """Обернене DCT: B = C^T * F * C."""
    blocks = np.einsum("ji,abjk,kl->abil", c, coeffs, c)
    return merge_blocks(blocks) + 128.0


# DWT (вейвлет Хаара)
def haar_step_1d(a):
    """
    Один крок перетворення Хаара вздовж останньої осі.

    Сусідні відліки замінюються на півсуму (апроксимація) і піврізницю (деталі). Ділення на корінь з двох робить перетворення ортонормованим, тобто таким, що зберігає енергію сигналу.
    """
    even, odd = a[..., 0::2], a[..., 1::2]
    low = (even + odd) / np.sqrt(2.0)
    high = (even - odd) / np.sqrt(2.0)
    return np.concatenate([low, high], axis=-1)


def ihaar_step_1d(a):
    """Обернений крок: з півсум і піврізниць відновлюємо пари відліків."""
    half = a.shape[-1] // 2
    low, high = a[..., :half], a[..., half:]
    out = np.empty(a.shape, dtype=a.dtype)
    out[..., 0::2] = (low + high) / np.sqrt(2.0)
    out[..., 1::2] = (low - high) / np.sqrt(2.0)
    return out


def dwt2(img, levels):
    """Пряме 2D-перетворення Хаара.

    На кожному рівні обробляємо спочатку рядки, потім стовпці — зображення розпадається на чотири частини: LL (зменшена копія), LH, HL, HH (деталі).
    Наступний рівень застосовується лише до LL у лівому верхньому куті.
    """
    out = img.astype(np.float64).copy()
    size = out.shape[0]
    for _ in range(levels):
        part = out[:size, :size]
        part = haar_step_1d(part)        # по рядках
        part = haar_step_1d(part.T).T    # по стовпцях
        out[:size, :size] = part
        size //= 2
    return out


def idwt2(coeffs, levels):
    """Обернене 2D-перетворення: ті самі кроки у зворотному порядку."""
    out = coeffs.copy()
    size = out.shape[0] // (2 ** (levels - 1))
    for _ in range(levels):
        part = out[:size, :size]
        part = ihaar_step_1d(part.T).T   # спершу стовпці
        part = ihaar_step_1d(part)       # потім рядки
        out[:size, :size] = part
        size *= 2
    return out



# стиснення та якість
def keep_largest(coeffs, keep_ratio):
    """
    Залишає задану частку найбільших за модулем коефіцієнтів.
    Решта обнулюється — це і є втрата інформації. Повертає оброблені коефіцієнти та фактичну кількість ненульових серед них.
    """
    magnitudes = np.abs(coeffs).ravel()
    total = magnitudes.size
    keep = max(1, int(round(total * keep_ratio)))
    if keep >= total:
        return coeffs.copy(), int(np.count_nonzero(coeffs))
    # np.partition знаходить поріг без повного сортування масиву
    threshold = np.partition(magnitudes, total - keep)[total - keep]
    result = np.where(np.abs(coeffs) >= threshold, coeffs, 0.0)
    return result, int(np.count_nonzero(result))


def psnr(original, restored):
    """Пікове відношення сигнал/шум у децибелах для 8-бітних зображень."""
    mse = np.mean((original.astype(np.float64) - restored.astype(np.float64)) ** 2)
    if mse == 0:
        return float("inf")
    return 10.0 * np.log10(255.0 ** 2 / mse)


def to_image(arr):
    """Обмежує значення діапазоном [0, 255] і переводить у 8 біт."""
    return np.clip(np.rint(arr), 0, 255).astype(np.uint8)


def load_grayscale(path, size=IMAGE_SIZE):
    """Читає файл, переводить у відтінки сірого і зводить до квадрата size*size.

    Спочатку обрізаємо по центру до квадрата, щоб не спотворити пропорції, і лише потім масштабуємо. 
    Розмір має бути кратним 8 (для блоків DCT) і степенем двійки (для рівнів перетворення Хаара).
    """
    img = Image.open(path).convert("L")
    side = min(img.size)
    left = (img.width - side) // 2
    top = (img.height - side) // 2
    img = img.crop((left, top, left + side, top + side))
    img = img.resize((size, size), Image.LANCZOS)
    return np.asarray(img, dtype=np.float64)


def to_pixmap(arr, size=PANEL_SIZE):
    """Перетворює масив NumPy на зображення для показу у вікні."""
    arr = np.ascontiguousarray(arr, dtype=np.uint8)
    h, w = arr.shape
    image = QImage(arr.tobytes(), w, h, w, QImage.Format_Grayscale8)
    return QPixmap.fromImage(image).scaled(
        size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation
    )


# Покроковий слід
def coefficient_map(block, kept_block):
    """Текстова карта блока: де коефіцієнт залишився, а де його обнулено.

    Показує наочно, що виживають переважно низькі частоти —    лівий верхній кут блока
    """
    rows = []
    for y in range(block.shape[0]):
        cells = []
        for x in range(block.shape[1]):
            cells.append("#" if kept_block[y, x] != 0 else "·")
        rows.append("   " + " ".join(cells))
    return "\n".join(rows)


def energy_share(coeffs, kept):
    """яка частка енергії сигналу лишилася після відкидання коефіцієнтів."""
    total = np.sum(coeffs ** 2)
    return np.sum(kept ** 2) / total if total else 1.0


def busiest_block(image):
    """Знаходить блок 8×8 з найбільшою дисперсією яскравості.
    На рівній ділянці (небо, стіна) усі кроки перетворення дають "нецікаві" числа, тому для показу беремо найдетальніший блок
    """
    blocks = split_blocks(image)
    variances = blocks.reshape(blocks.shape[0], blocks.shape[1], -1).var(axis=2)
    by, bx = np.unravel_index(np.argmax(variances), variances.shape)
    return int(by), int(bx)


def print_trace(image, keep_ratio, levels, c):
    """Друкує у консоль проміжні значення обох алгоритмів.

    Потрібно, щоб показати хід обчислень на конкретних числах:
    що саме відбувається з блоком 8×8 і з рядком пікселів на кожному кроці.
    """
    np.set_printoptions(precision=2, suppress=True, linewidth=120)
    line = "=" * 68
    by, bx = busiest_block(image)
    row0, col0 = by * BLOCK, bx * BLOCK

    print(f"\n{line}")
    print(f"ХІД ОБЧИСЛЕНЬ   (збережено коефіцієнтів: {keep_ratio:.1%})")
    print(f"Для показу обрано найдетальніший блок: рядок {row0}, стовпець {col0}")
    print(line)

    # -- DCT --
    block = image[row0:row0 + BLOCK, col0:col0 + BLOCK]
    print("\n--- DCT ---")
    print("1. Обраний блок 8×8, яскравість пікселів:")
    print(block)
    print("\n2. Той самий блок після віднімання 128 (центрування діапазону):")
    print(block - 128.0)
    print("\n3. Матриця перетворення C (рядок — частота, стовпець — відлік):")
    print(c)

    coeffs = dct2_blocks(image, c)
    print("\n4. Коефіцієнти після прямого DCT, F = C · B · Cᵀ")
    print("   Лівий верхній елемент — DC-коефіцієнт, середня яскравість блока:")
    print(coeffs[by, bx])

    kept, nonzero = keep_largest(coeffs, keep_ratio)
    total = coeffs.size
    print("\n5. Ті самі коефіцієнти після відкидання малих за модулем:")
    print(kept[by, bx])
    print("\n   Карта блока (# — коефіцієнт залишено, · — обнулено):")
    print(coefficient_map(coeffs[by, bx], kept[by, bx]))
    print(f"\n   По всьому зображенню залишилось {nonzero} з {total} "
          f"({nonzero / total:.1%}) коефіцієнтів,")
    print(f"   але вони несуть {energy_share(coeffs, kept):.2%} енергії сигналу —")
    print("   саме тому відкидання більшості коефіцієнтів майже не псує зображення.")

    restored = idct2_blocks(kept, c)
    restored_block = restored[row0:row0 + BLOCK, col0:col0 + BLOCK]
    print("\n6. Блок після оберненого DCT і додавання 128:")
    print(restored_block)
    print(f"   Найбільша похибка в цьому блоці: "
          f"{np.max(np.abs(block - restored_block)):.2f} рівня яскравості")
    print(f"   PSNR усього зображення: {psnr(image, to_image(restored)):.2f} дБ")

    # -- Хаар --
    print("\n--- DWT (вейвлет Хаара) ---")
    row = image[row0, col0:col0 + 8]
    print(f"1. Перші 8 пікселів рядка {row0} того самого блока:")
    print(row)

    step = haar_step_1d(row)
    print("\n2. Після одного кроку: спочатку спільні складові, потім деталі.")
    print(f"   Спільні складові: {step[:4]}")
    print(f"   Деталі:           {step[4:]}")
    print("   Перевірка першої пари вручну: "
          f"({row[0]:.0f} + {row[1]:.0f}) / √2 = {(row[0] + row[1]) / np.sqrt(2):.2f}")

    dwt_coeffs = dwt2(image, levels)
    half = dwt_coeffs.shape[0] // 2
    bands = {
        "LL (структура)": dwt_coeffs[:half, :half],
        "LH (горизонталі)": dwt_coeffs[:half, half:],
        "HL (вертикалі)": dwt_coeffs[half:, :half],
        "HH (діагоналі)": dwt_coeffs[half:, half:],
    }
    whole = np.sum(dwt_coeffs ** 2)
    print(f"\n3. Розподіл енергії по областях першого рівня "
          f"(усього рівнів: {levels}):")
    for name, band in bands.items():
        print(f"   {name:<20} {np.sum(band ** 2) / whole:>7.3%}")
    print("   Майже вся енергія в LL — тому деталі можна відкидати найперше.")

    dwt_kept, dwt_nonzero = keep_largest(dwt_coeffs, keep_ratio)
    print(f"\n4. Після відкидання: залишилось {dwt_nonzero} з {dwt_coeffs.size} "
          f"({dwt_nonzero / dwt_coeffs.size:.1%}),")
    print(f"   вони несуть {energy_share(dwt_coeffs, dwt_kept):.2%} енергії.")
    print("   Скільки коефіцієнтів вціліло в кожній області:")
    kept_bands = {
        "LL (структура)": dwt_kept[:half, :half],
        "LH (горизонталі)": dwt_kept[:half, half:],
        "HL (вертикалі)": dwt_kept[half:, :half],
        "HH (діагоналі)": dwt_kept[half:, half:],
    }
    for name, band in kept_bands.items():
        survived = np.count_nonzero(band)
        print(f"   {name:<20} {survived:>8} з {band.size} ({survived / band.size:>6.1%})")

    dwt_restored = idwt2(dwt_kept, levels)
    print("\n5. Ті самі 8 пікселів після оберненого перетворення:")
    print(dwt_restored[row0, col0:col0 + 8])
    print("   Для порівняння — початкові:")
    print(row)
    print(f"   PSNR усього зображення: {psnr(image, to_image(dwt_restored)):.2f} дБ")
    print(f"{line}\n")

    np.set_printoptions()  # повертаємо стандартні налаштування виведення


# Базовий інтерфейс
class ImagePanel(QWidget):
    """Одна колонка результату: заголовок, зображення та підпис із числами."""

    def __init__(self, title):
        super().__init__()
        self.title_label = QLabel(title)
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet("font-weight: bold; font-size: 14px;")

        self.image_label = QLabel("немає зображення")
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setFixedSize(PANEL_SIZE, PANEL_SIZE)
        self.image_label.setFrameShape(QFrame.Box)

        self.info_label = QLabel("—")
        self.info_label.setAlignment(Qt.AlignCenter)

        layout = QVBoxLayout(self)
        layout.addWidget(self.title_label)
        layout.addWidget(self.image_label)
        layout.addWidget(self.info_label)

    def show_image(self, arr, info):
        self.image_label.setPixmap(to_pixmap(arr))
        self.info_label.setText(info)


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Лабораторна №3 — стиснення з втратами (DCT / DWT)")

        # вихідні дані та заздалегідь обчислені коефіцієнти перетворень
        self.image_path = None
        self.original = None        # зображення у відтінках сірого, float64
        self.dct_coeffs = None      # коефіцієнти DCT усього зображення
        self.dwt_coeffs = None      # коефіцієнти перетворення Хаара
        self.dct_m = dct_matrix()   # матриця DCT рахується один раз

        # верхній рядок керування
        self.open_btn = QPushButton("Відкрити зображення")
        self.file_label = QLabel("файл не вибрано")

        self.levels_spin = QSpinBox()
        self.levels_spin.setRange(1, 5)
        self.levels_spin.setValue(DEFAULT_LEVELS)
        self.levels_spin.setToolTip("Кількість рівнів розкладу Хаара")

        self.experiment_btn = QPushButton("Провести експерименти")
        self.experiment_btn.setEnabled(False)

        self.trace_btn = QPushButton("Хід обчислень у консоль")
        self.trace_btn.setEnabled(False)
        self.trace_btn.setToolTip(
            "Друкує проміжні значення обох алгоритмів у вікно термінала"
        )

        top_row = QHBoxLayout()
        top_row.addWidget(self.open_btn)
        top_row.addWidget(self.file_label, 1)
        top_row.addWidget(QLabel("Рівнів Хаара:"))
        top_row.addWidget(self.levels_spin)
        top_row.addWidget(self.experiment_btn)
        top_row.addWidget(self.trace_btn)

        # повзунок (для рівня стиснення)
        # Значення повзунка — десяті частки відсотка, тому 1000 = 100 %
        self.ratio_slider = QSlider(Qt.Horizontal)
        self.ratio_slider.setRange(1, 1000)
        self.ratio_slider.setValue(100)          # стартова частка 10 %
        self.ratio_slider.setEnabled(False)
        self.ratio_label = QLabel()
        self.ratio_label.setMinimumWidth(240)

        preset_row = QHBoxLayout()
        preset_row.addWidget(QLabel("Швидкий вибір:"))
        for percent in (50, 25, 10, 5, 1):
            btn = QPushButton(f"{percent} %")
            btn.setFixedWidth(60)
            # lambda із значенням за замовчуванням, щоб кожна кнопка запам'ятала власне значення, а не останнє у циклі
            btn.clicked.connect(
                lambda _checked=False, p=percent: self.ratio_slider.setValue(p * 10)
            )
            preset_row.addWidget(btn)
        preset_row.addStretch()

        slider_row = QHBoxLayout()
        slider_row.addWidget(self.ratio_label)
        slider_row.addWidget(self.ratio_slider, 1)

        # 3 панельки результатів
        self.original_panel = ImagePanel("Оригінал")
        self.dct_panel = ImagePanel("DCT (блоки 8×8)")
        self.dwt_panel = ImagePanel("DWT (вейвлет Хаара)")

        panels_row = QHBoxLayout()
        panels_row.addWidget(self.original_panel)
        panels_row.addWidget(self.dct_panel)
        panels_row.addWidget(self.dwt_panel)

        self.status_label = QLabel("Відкрийте зображення, щоб почати.")

        layout = QVBoxLayout(self)
        layout.addLayout(top_row)
        layout.addLayout(slider_row)
        layout.addLayout(preset_row)
        layout.addLayout(panels_row)
        layout.addWidget(self.status_label)

        # сигнали
        self.open_btn.clicked.connect(self.open_image)
        self.experiment_btn.clicked.connect(self.run_experiments)
        self.trace_btn.clicked.connect(self.show_trace)
        self.ratio_slider.valueChanged.connect(self.update_result)
        self.levels_spin.valueChanged.connect(self.on_levels_changed)

        self.update_ratio_label()

    # едішинал
    def keep_ratio(self):
        """Поточна частка збережених коефіцієнтів як число від 0 до 1."""
        return self.ratio_slider.value() / 1000.0

    def update_ratio_label(self):
        self.ratio_label.setText(
            f"Збережено коефіцієнтів: {self.keep_ratio() * 100:.1f} %"
        )

    def on_levels_changed(self):
        """Зміна кількості рівнів вимагає перерахунку коефіцієнтів Хаара."""
        if self.original is None:
            return
        self.dwt_coeffs = dwt2(self.original, self.levels_spin.value())
        self.update_result()

    # дії
    def open_image(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Обрати зображення", "",
            "Зображення (*.png *.jpg *.jpeg *.bmp *.tif *.tiff);;Усі файли (*)",
        )
        if not path:
            return
        try:
            self.original = load_grayscale(path)
        except Exception as error:
            QMessageBox.warning(self, "Не вдалося відкрити файл", str(error))
            return

        self.image_path = path
        self.file_label.setText(Path(path).name)

        # Прямі перетворення виконуються один раз після завантаження.
        self.dct_coeffs = dct2_blocks(self.original, self.dct_m)
        self.dwt_coeffs = dwt2(self.original, self.levels_spin.value())

        self.ratio_slider.setEnabled(True)
        self.experiment_btn.setEnabled(True)
        self.trace_btn.setEnabled(True)
        self.original_panel.show_image(
            to_image(self.original), f"{IMAGE_SIZE}×{IMAGE_SIZE}, 8 біт"
        )
        self.update_result()

    def restore(self, keep_ratio):
        """Відновлює зображення обома методами для заданої частки коефіцієнтів.
        Повертає пари (зображення, кількість ненульових коефіцієнтів).
        """
        dct_kept, dct_nonzero = keep_largest(self.dct_coeffs, keep_ratio)
        dct_image = to_image(idct2_blocks(dct_kept, self.dct_m))

        dwt_kept, dwt_nonzero = keep_largest(self.dwt_coeffs, keep_ratio)
        dwt_image = to_image(idwt2(dwt_kept, self.levels_spin.value()))

        return (dct_image, dct_nonzero), (dwt_image, dwt_nonzero)

    def update_result(self):
        self.update_ratio_label()
        if self.original is None:
            return

        ratio = self.keep_ratio()
        (dct_image, dct_nonzero), (dwt_image, dwt_nonzero) = self.restore(ratio)
        total = self.original.size

        self.dct_panel.show_image(
            dct_image,
            f"PSNR: {psnr(self.original, dct_image):.2f} дБ\n"
            f"ненульових: {dct_nonzero:,} з {total:,}".replace(",", " "),
        )
        self.dwt_panel.show_image(
            dwt_image,
            f"PSNR: {psnr(self.original, dwt_image):.2f} дБ\n"
            f"ненульових: {dwt_nonzero:,} з {total:,}".replace(",", " "),
        )
        # Коефіцієнт стиснення рахуємо як відношення загальної кількості коефіцієнтів до кількості ненульових, а не як розмір файлу
        self.status_label.setText(
            f"Коефіцієнт стиснення за кількістю коефіцієнтів: "
            f"DCT ≈ {total / max(1, dct_nonzero):.1f}×, "
            f"DWT ≈ {total / max(1, dwt_nonzero):.1f}×"
        )

    def run_experiments(self):
        """Проганяє кілька рівнів стиснення, показує таблицю і зберігає результати."""
        total = self.original.size
        lines = [
            f"Зображення: {Path(self.image_path).name}   "
            f"({IMAGE_SIZE}×{IMAGE_SIZE}, рівнів Хаара: {self.levels_spin.value()})",
            "",
            f"{'Частка':>8} {'Ненульових':>12} {'Стиснення':>10} "
            f"{'PSNR DCT':>10} {'PSNR DWT':>10}",
            "-" * 54,
        ]
        rows = []
        montage = []
        for ratio in EXPERIMENT_RATIOS:
            (dct_image, dct_nonzero), (dwt_image, dwt_nonzero) = self.restore(ratio)
            dct_psnr = psnr(self.original, dct_image)
            dwt_psnr = psnr(self.original, dwt_image)
            lines.append(
                f"{ratio:>7.1%} {dct_nonzero:>12,} {total / dct_nonzero:>9.1f}× "
                f"{dct_psnr:>10.2f} {dwt_psnr:>10.2f}".replace(",", " ")
            )
            rows.append((ratio, dct_nonzero, dwt_nonzero, dct_psnr, dwt_psnr))
            montage.append(
                np.hstack([to_image(self.original), dct_image, dwt_image])
            )

        out_dir = Path(self.image_path).parent / "lab3_results"
        out_dir.mkdir(exist_ok=True)
        csv_path = out_dir / "experiments.csv"
        with open(csv_path, "w", encoding="utf-8") as f:
            f.write("keep_ratio,dct_nonzero,dwt_nonzero,psnr_dct,psnr_dwt\n")
            for ratio, dct_nz, dwt_nz, dct_p, dwt_p in rows:
                f.write(f"{ratio},{dct_nz},{dwt_nz},{dct_p:.4f},{dwt_p:.4f}\n")
        montage_path = out_dir / "montage.png"
        Image.fromarray(np.vstack(montage)).save(montage_path)

        lines += ["", f"Збережено: {csv_path}", f"Збережено: {montage_path}"]
        self.show_report("\n".join(lines))

    def show_trace(self):
        """Друкує покроковий хід обчислень для поточного рівня стиснення."""
        print_trace(self.original, self.keep_ratio(),
                    self.levels_spin.value(), self.dct_m)
        self.status_label.setText(
            "Хід обчислень надруковано у вікні термінала, де запущено програму."
        )

    def show_report(self, text):
        dialog = QDialog(self)
        dialog.setWindowTitle("Результати експериментів")
        dialog.resize(640, 420)
        view = QTextEdit()
        view.setReadOnly(True)
        view.setStyleSheet("font-family: Menlo, Courier New, monospace;")
        view.setText(text)
        close_btn = QPushButton("Закрити")
        close_btn.clicked.connect(dialog.accept)
        layout = QVBoxLayout(dialog)
        layout.addWidget(view)
        layout.addWidget(close_btn)
        dialog.exec()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
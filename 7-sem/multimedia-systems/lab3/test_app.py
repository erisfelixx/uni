"""
Перевірка власних реалізацій DCT і перетворення Хаара з app.py.

Перевірка проти еталонного DCT зі SciPy виконується лише якщо SciPy встановлено. 
У самій програмі SciPy не використовується — він потрібен тільки тут, 
щоб показати, що власна реалізація дає ті самі числа!!
"""


import tempfile
from pathlib import Path

import numpy as np
from PIL import Image

import app

TOLERANCE = 1e-10          # допустима похибка обчислень
rng = np.random.default_rng(42)


def random_image(size=app.IMAGE_SIZE):
    """Випадкове зображення потрібного розміру у діапазоні яскравості 0..255."""
    return rng.uniform(0, 255, (size, size))


# DCT
def test_dct_matrix_is_orthonormal():
    """C * C^T = I, тому обернене перетворення — це множення на C^T."""
    c = app.dct_matrix()
    assert np.allclose(c @ c.T, np.eye(app.BLOCK), atol=TOLERANCE)


def test_dct_matches_reference():
    """Власне DCT збігається з еталонним DCT-II зі SciPy."""
    try:
        from scipy.fftpack import dct as reference_dct
    except ImportError:
        print("   (пропущено: SciPy не встановлено)")
        return
    c = app.dct_matrix()
    block = rng.uniform(0, 255, (app.BLOCK, app.BLOCK)) - 128.0
    mine = c @ block @ c.T
    # еталон: DCT-II по стовпцях, потім по рядках, з нормуванням "ortho"
    reference = reference_dct(reference_dct(block.T, norm="ortho").T, norm="ortho")
    assert np.allclose(mine, reference, atol=TOLERANCE)


def test_dct_reconstructs_exactly():
    """Без відкидання коефіцієнтів DCT відновлює зображення точно."""
    image = random_image()
    c = app.dct_matrix()
    restored = app.idct2_blocks(app.dct2_blocks(image, c), c)
    assert np.allclose(image, restored, atol=TOLERANCE)


def test_dct_preserves_energy():
    """Сума квадратів коефіцієнтів дорівнює сумі квадратів відліків."""
    image = random_image()
    c = app.dct_matrix()
    blocks_energy = np.sum((app.split_blocks(image) - 128.0) ** 2)
    coeffs_energy = np.sum(app.dct2_blocks(image, c) ** 2)
    assert np.isclose(blocks_energy, coeffs_energy)


def test_blocks_split_and_merge():
    """Розрізання на блоки 8x8 і зворотне збирання не змінюють зображення."""
    image = random_image(64)
    assert np.array_equal(image, app.merge_blocks(app.split_blocks(image)))


# DWT
def test_haar_reconstructs_exactly():
    """Перетворення Хаара відновлює зображення точно на всіх рівнях."""
    image = random_image()
    for levels in (1, 2, 3, 4, 5):
        restored = app.idwt2(app.dwt2(image, levels), levels)
        assert np.allclose(image, restored, atol=TOLERANCE), f"рівень {levels}"


def test_haar_preserves_energy():
    """Перетворення ортонормоване, тому енергія зберігається."""
    image = random_image()
    assert np.isclose(np.sum(image ** 2), np.sum(app.dwt2(image, 3) ** 2))


def test_haar_low_frequency_is_average():
    """Низькочастотний коефіцієнт дорівнює середньому чотирьох пікселів, помноженому на два.

    Множник два — наслідок нормування на корінь з двох по рядках і по стовпцях.
    """
    image = np.array([[10.0, 20.0], [30.0, 40.0]])
    coeffs = app.dwt2(image, 1)
    assert np.isclose(coeffs[0, 0], image.mean() * 2)


def test_haar_detail_of_flat_image_is_zero():
    """У рівномірного зображення немає деталей — усі високочастотні нулі."""
    coeffs = app.dwt2(np.full((8, 8), 128.0), 3)
    assert np.isclose(coeffs[0, 0], 128.0 * 8)      # уся енергія в одному коефіцієнті
    assert np.allclose(coeffs.ravel()[1:], 0.0, atol=TOLERANCE)


# стиснення
def test_keep_largest_keeps_expected_count():
    """Лишається задана частка коефіцієнтів, і саме найбільші за модулем."""
    coeffs = np.array([5.0, -9.0, 1.0, 0.0, 3.0, -7.0, 2.0, 8.0])
    kept, nonzero = app.keep_largest(coeffs, 0.5)
    assert nonzero == 4
    assert set(kept[kept != 0]) == {-9.0, 8.0, -7.0, 5.0}


def test_keep_largest_edge_cases():
    """Межові випадки: усі нулі, повне збереження, мінімальна частка."""
    _, nonzero = app.keep_largest(np.zeros(10), 0.5)
    assert nonzero == 0
    _, nonzero = app.keep_largest(np.arange(1.0, 11.0), 1.0)
    assert nonzero == 10
    _, nonzero = app.keep_largest(np.arange(1.0, 11.0), 0.0)
    assert nonzero == 1          # щонайменше один коефіцієнт лишаємо завжди


def test_more_coefficients_give_better_quality():
    """Чим більша частка збережених коефіцієнтів, тим вищий PSNR.

    Це головна перевірка того, що стиснення поводиться осмислено.
    """
    image = app.to_image(gradient_image()).astype(np.float64)
    c = app.dct_matrix()
    dct_coeffs = app.dct2_blocks(image, c)
    dwt_coeffs = app.dwt2(image, 3)

    dct_scores, dwt_scores = [], []
    for ratio in (0.01, 0.05, 0.10, 0.25, 0.50):
        kept, _ = app.keep_largest(dct_coeffs, ratio)
        dct_scores.append(app.psnr(image, app.to_image(app.idct2_blocks(kept, c))))
        kept, _ = app.keep_largest(dwt_coeffs, ratio)
        dwt_scores.append(app.psnr(image, app.to_image(app.idwt2(kept, 3))))

    assert dct_scores == sorted(dct_scores), f"DCT: {dct_scores}"
    assert dwt_scores == sorted(dwt_scores), f"DWT: {dwt_scores}"


def gradient_image(size=app.IMAGE_SIZE):
    """Плавне зображення з кількома деталями — ближче до фотографії,
    ніж білий шум, на якому стиснення не має сенсу."""
    y, x = np.mgrid[0:size, 0:size]
    image = 128 + 100 * np.sin(x / 40.0) * np.cos(y / 55.0)
    image[size // 4: size // 2, size // 4: size // 2] = 20     # темний квадрат
    return np.clip(image, 0, 255)


# PSNR
def test_psnr_identical_is_infinite():
    """PSNR однакових зображень нескінченний, бо похибка нульова."""
    image = random_image()
    assert app.psnr(image, image) == float("inf")


def test_psnr_known_values():
    """PSNR збігається з відомими еталонними значеннями.

    Максимальна можлива різниця дає рівно 0 дБ, різниця в одну одиницю — 48.13 дБ.
    """
    black = np.zeros((4, 4))
    white = np.full((4, 4), 255.0)
    assert np.isclose(app.psnr(black, white), 0.0)
    assert np.isclose(app.psnr(black, np.ones((4, 4))), 10 * np.log10(255.0 ** 2))


def test_psnr_decreases_with_noise():
    """Сильніший шум — нижчий PSNR."""
    image = random_image(64)
    weak = app.psnr(image, image + rng.normal(0, 1, image.shape))
    strong = app.psnr(image, image + rng.normal(0, 10, image.shape))
    assert weak > strong


# вхідні дані
def test_load_grayscale_normalizes_input():
    """Кольорове прямокутне зображення зводиться до квадрата у відтінках сірого."""
    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder) / "test.png"
        colour = rng.integers(0, 256, (300, 500, 3), dtype=np.uint8)
        Image.fromarray(colour).save(path)

        result = app.load_grayscale(path)
        assert result.shape == (app.IMAGE_SIZE, app.IMAGE_SIZE)
        assert result.dtype == np.float64
        assert 0.0 <= result.min() and result.max() <= 255.0


def test_full_pipeline_without_losses():
    """Зі збереженням усіх коефіцієнтів обидва методи відновлюють оригінал точно.

    Отже, втрати вносить саме відкидання коефіцієнтів, а не перетворення.
    """
    image = app.to_image(gradient_image()).astype(np.float64)
    c = app.dct_matrix()

    kept, _ = app.keep_largest(app.dct2_blocks(image, c), 1.0)
    assert np.array_equal(image, app.to_image(app.idct2_blocks(kept, c)))

    kept, _ = app.keep_largest(app.dwt2(image, 3), 1.0)
    assert np.array_equal(image, app.to_image(app.idwt2(kept, 3)))


# запуск
def main():
    tests = [(name, value) for name, value in sorted(globals().items())
             if name.startswith("test_") and callable(value)]
    passed = 0
    print(f"Запускаю {len(tests)} перевірок\n")
    for name, test in tests:
        title = (test.__doc__ or name).strip().splitlines()[0]
        try:
            test()
        except AssertionError as error:
            print(f"[ПОМИЛКА] {name}\n   {title}\n   {error}")
        except Exception as error:
            print(f"[ЗБІЙ]    {name}\n   {type(error).__name__}: {error}")
        else:
            passed += 1
            print(f"[ok] {title}")
    print(f"\nПройдено {passed} із {len(tests)}")
    return 0 if passed == len(tests) else 1


if __name__ == "__main__":
    raise SystemExit(main())
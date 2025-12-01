import numpy as np
import matplotlib.pyplot as plt

# -------------------------------------------------
# Точна функція та її похідні
# -------------------------------------------------

def f(x):
    """f(x) = tan(x)"""
    return np.tan(x)

def df(x):
    """Перша похідна: f'(x) = 1 / cos^2(x)"""
    return 1.0 / (np.cos(x) ** 2)

def df2(x):
    """Друга похідна: f''(x) = 2 * tan(x) / cos^2(x)"""
    return 2.0 * np.tan(x) / (np.cos(x) ** 2)


# -------------------------------------------------
# Розв’язання тридіагональної СЛАР (метод прогонки)
# -------------------------------------------------

def solve_tridiagonal(A, b, verbose=True):
    """
    A - (m x m), ненульові лише три діагоналі.
    b - вектор правих частин.
    Повертає вектор c (це і є внутрішні c_i з методички).
    """
    m = len(b)
    alpha = np.zeros(m)
    beta = np.zeros(m)

    if verbose:
        print("\n=== РОЗВ’ЯЗАННЯ СЛАР МЕТОДОМ ПРОГОНКИ ===")
        print("Матриця A:")
        for i in range(m):
            print(" ".join(f"{A[i, j]:10.6f}" for j in range(m)))
        print("Вектор b:")
        for i in range(m):
            print(f"b[{i+1}] = {b[i]:.6f}")

    # прямий хід
    alpha[0] = -A[0, 1] / A[0, 0]
    beta[0]  =  b[0]    / A[0, 0]

    for i in range(1, m):
        denom = A[i, i] + A[i, i-1] * alpha[i-1]
        if i < m - 1:
            alpha[i] = -A[i, i+1] / denom
        beta[i] = (b[i] - A[i, i-1] * beta[i-1]) / denom

    # зворотний хід
    c_internal = np.zeros(m)
    c_internal[-1] = beta[-1]
    for i in range(m - 2, -1, -1):
        c_internal[i] = alpha[i] * c_internal[i+1] + beta[i]

    return c_internal


# -------------------------------------------------
# Побудова природного кубічного сплайна
# -------------------------------------------------

def build_natural_cubic_spline(x_nodes, f_nodes, verbose=True):
    """
    Будує природний кубічний інтерполяційний сплайн для вузлів (x_i, f_i).

    Повертає:
      - a_poly[i], b_poly[i], c_poly[i], d_poly[i] – коефіцієнти поліномів

    Сплайн на [x_i, x_{i+1}]:
      S_i(x) = a_i + b_i (x - x_i) + c_i (x - x_i)^2 + d_i (x - x_i)^3.
    """

    N = len(x_nodes)  # кількість вузлів: i = 0..N-1

    if verbose:
        print("==============================================")
        print("         ПОБУДОВА ПРИРОДНОГО КУБІЧНОГО СПЛАЙНА")
        print("==============================================")
        print(f"Кількість вузлів N = {N}")
        print("\nВузли (x_i, f_i):")
        for i in range(N):
            print(f"i = {i:2d}, x[{i}] = {x_nodes[i]: .6f}, f[{i}] = {f_nodes[i]: .6f}")

    # --- кроки h_i = x_i - x_{i-1}, i = 1..N-1 ---
    h = np.zeros(N)
    for i in range(1, N):
        h[i] = x_nodes[i] - x_nodes[i-1]

    if verbose:
        print("\nКроки h_i = x_i - x_{i-1}:")
        for i in range(1, N):
            print(f"h[{i}] = x[{i}] - x[{i-1}] = {x_nodes[i]: .6f} - {x_nodes[i-1]: .6f} = {h[i]: .6f}")

    # --- формуємо СЛАР для внутрішніх c_i, i = 1..N-2 ---
   
    m = N - 2  # кількість внутрішніх невідомих: c_1..c_{N-2}

    if m > 0:
        A = np.zeros((m, m))
        b_vec = np.zeros(m)

        for i in range(1, N - 1):   # i = 1..N-2
            hi   = h[i]
            hip1 = h[i+1]
            k = i - 1               # рядок у A,b_vec: 0..m-1

            if k > 0:
                A[k, k-1] = hi
            A[k, k] = 2.0 * (hi + hip1)
            if k < m - 1:
                A[k, k+1] = hip1

            b_vec[k] = 6.0 * (
                (f_nodes[i+1] - f_nodes[i]) / hip1
                - (f_nodes[i]   - f_nodes[i-1]) / hi
            )

        # розв’язуємо тридіагональну систему
        c_internal = solve_tridiagonal(A, b_vec, verbose=verbose)

        # повний масив c_i: c_0..c_{N-1}
        c_nodes = np.zeros(N)
        c_nodes[1:N-1] = c_internal
    else:
        c_nodes = np.zeros(N)

    if verbose:
        print("\nКоефіцієнти c_i, S''(x_i)):")
        for i in range(N):
            print(f"c[{i}] = {c_nodes[i]:.6f}")
        print("\n(Для природного сплайна c[0] = c[N-1] = 0 — це граничні умови S''(x_0)=S''(x_N)=0)")

    # --- коефіцієнти поліномів на кожному відрізку ---
    a_poly = []
    b_poly = []
    c_poly = []
    d_poly = []

    if verbose:
        print("\nКОЕФІЦІЄНТИ ПОЛІНОМІВ a_i, b_i, c_i, d_i ДЛЯ [x_i, x_{i+1}]:")

    for i in range(N - 1):
        hi = x_nodes[i+1] - x_nodes[i]
        a_i = f_nodes[i]
        b_i = (f_nodes[i+1] - f_nodes[i]) / hi - (2.0 * c_nodes[i] + c_nodes[i+1]) * hi / 6.0
        c_i = c_nodes[i] / 2.0
        d_i = (c_nodes[i+1] - c_nodes[i]) / (6.0 * hi)

        a_poly.append(a_i)
        b_poly.append(b_i)
        c_poly.append(c_i)
        d_poly.append(d_i)

        if verbose:
            print(f"\nВідрізок [{i}]: [{x_nodes[i]: .6f}, {x_nodes[i+1]: .6f}]")
            print(f"a[{i}] = {a_i:.6f}")
            print(f"b[{i}] = {b_i:.6f}")
            print(f"c[{i}] = {c_i:.6f}")
            print(f"d[{i}] = {d_i:.6f}")

    if verbose:
        # --- БЛОК 1: НЕРОЗКРИТИЙ ВИГЛЯД ---
        print("\n" + "="*75)
        print("1. ОТРИМАНІ СПЛАЙНИ НА КОЖНОМУ ВІДРІЗКУ")
        print("="*75)
        for i in range(N - 1):
            xi = x_nodes[i]
            print(f"Відрізок {i+1} [{x_nodes[i]:.6f}; {x_nodes[i+1]:.6f}]:")
            print(f" S(x) = {a_poly[i]:.6f}"
                  f" {b_poly[i]:+.6f}(x - {xi:.6f})"
                  f" {c_poly[i]:+.6f}(x - {xi:.6f})^2"
                  f" {d_poly[i]:+.6f}(x - {xi:.6f})^3")

        # --- БЛОК 2: РОЗКРИТИЙ (ЗВЕДЕНИЙ) ВИГЛЯД ---
        print("\n" + "="*75)
        print("2. СПЛАЙНИ У РОЗКРИТОМУ ВИГЛЯДІ: Ax^3 + Bx^2 + Cx + D")
        print("="*75)
        for i in range(N - 1):
            xi = x_nodes[i]
            
            # Обчислення коефіцієнтів для Ax^3 + Bx^2 + Cx + D
            A_exp = d_poly[i]
            B_exp = c_poly[i] - 3.0 * d_poly[i] * xi
            C_exp = b_poly[i] - 2.0 * c_poly[i] * xi + 3.0 * d_poly[i] * (xi**2)
            D_exp = a_poly[i] - b_poly[i] * xi + c_poly[i] * (xi**2) - d_poly[i] * (xi**3)
            
            print(f"Відрізок {i+1} [{x_nodes[i]:.6f}; {x_nodes[i+1]:.6f}]:")
            print(f" S(x) = {A_exp:.6f}x^3 {B_exp:+.6f}x^2 {C_exp:+.6f}x {D_exp:+.6f}")
            
    return a_poly, b_poly, c_poly, d_poly, c_nodes


# -------------------------------------------------
# Обчислення S(x), S'(x), S''(x)
# -------------------------------------------------

def _find_segment(x_val, x_nodes):
    """Знайти номер відрізка [x_i, x_{i+1}] для точки x_val."""
    N = len(x_nodes)
    if x_val <= x_nodes[0]:
        return 0
    if x_val >= x_nodes[-1]:
        return N - 2
    i = np.searchsorted(x_nodes, x_val) - 1
    if i < 0:
        i = 0
    if i > N - 2:
        i = N - 2
    return i

def evaluate_spline(x_val, x_nodes, a, b, c, d):
    i = _find_segment(x_val, x_nodes)
    dx = x_val - x_nodes[i]
    return a[i] + b[i]*dx + c[i]*dx**2 + d[i]*dx**3

def evaluate_spline_first_derivative(x_val, x_nodes, a, b, c, d):
    i = _find_segment(x_val, x_nodes)
    dx = x_val - x_nodes[i]
    return b[i] + 2.0*c[i]*dx + 3.0*d[i]*dx**2

def evaluate_spline_second_derivative(x_val, x_nodes, a, b, c, d):
    i = _find_segment(x_val, x_nodes)
    dx = x_val - x_nodes[i]
    return 2.0*c[i] + 6.0*d[i]*dx


# -------------------------------------------------
# Основна функція
# -------------------------------------------------

def main():
    # кількість вузлів 
    n = int(input("Введіть кількість вузлів (n >= 2, напр. 15): "))
    

    a_int, b_int = -0.5, 0.5
    x_nodes = np.linspace(a_int, b_int, n)
    f_nodes = f(x_nodes)

    # побудова сплайна +вивід
    a_poly, b_poly, c_poly, d_poly, c_nodes = build_natural_cubic_spline(
        x_nodes, f_nodes, verbose=True
    )

    # густі точки для графіків
    x_dense = np.linspace(a_int, b_int, 500)
    f_exact        = f(x_dense)
    f_exact_first  = df(x_dense)
    f_exact_second = df2(x_dense)

    f_spline        = np.array([evaluate_spline(x, x_nodes, a_poly, b_poly, c_poly, d_poly)
                                for x in x_dense])
    f_spline_first  = np.array([evaluate_spline_first_derivative(x, x_nodes, a_poly, b_poly, c_poly, d_poly)
                                for x in x_dense])
    f_spline_second = np.array([evaluate_spline_second_derivative(x, x_nodes, a_poly, b_poly, c_poly, d_poly)
                                for x in x_dense])

    # похибки
    error_function         = np.abs(f_exact - f_spline)
    error_first_derivative = np.abs(f_exact_first - f_spline_first)
    error_second_derivative= np.abs(f_exact_second - f_spline_second)

    # -------------------------------------------------
    # Графіки
    # -------------------------------------------------
    plt.figure(figsize=(12, 12))

    # 1) функція і сплайн
    plt.subplot(2, 2, 1)
    plt.plot(x_dense, f_exact, label="tan(x)")
    plt.plot(x_dense, f_spline, label="Сплайн S(x)", linestyle="--")
    plt.scatter(x_nodes, f_nodes, label="Вузли", marker="o")
    plt.title("Функція tan(x) та кубічний сплайн")
    plt.legend()
    plt.grid()

    # 2) перша похідна
    plt.subplot(2, 2, 2)
    plt.plot(x_dense, f_exact_first, label="Точна f'(x)")
    plt.plot(x_dense, f_spline_first, label="S'(x)", linestyle="--")
    plt.title("Перша похідна")
    plt.legend()
    plt.grid()

    # 3) друга похідна
    plt.subplot(2, 2, 3)
    plt.plot(x_dense, f_exact_second, label="Точна f''(x)")
    plt.plot(x_dense, f_spline_second, label="S''(x)", linestyle="--")
    plt.title("Друга похідна")
    plt.legend()
    plt.grid()

    # 4) похибки
    plt.subplot(2, 2, 4)
    plt.plot(x_dense, error_function,         label="|f - S|")
    plt.plot(x_dense, error_first_derivative, label="|f' - S'|")
    plt.plot(x_dense, error_second_derivative,label="|f'' - S''|")
    plt.title("Похибки")
    plt.legend()
    plt.grid()

    plt.tight_layout()
    plt.savefig("spline_tan_full_analysis.png")
    plt.show()


if __name__ == "__main__":
    main()

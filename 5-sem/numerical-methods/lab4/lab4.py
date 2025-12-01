import math
from typing import List, Tuple
import matplotlib.pyplot as plt

# ============================================
#  Клас полінома (ступенева форма)
# ============================================

class Polynomial:
    """Поліном у степеневій формі: P(x) = c[0] + c[1] x + c[2] x^2 + ..."""

    def __init__(self, coeffs=None):
        if coeffs is None:
            coeffs = [0.0]
        self.coeffs = list(coeffs)
        self._trim()

    @staticmethod
    def constant(c: float) -> "Polynomial":
        return Polynomial([c])

    @staticmethod
    def linear(c0: float, c1: float) -> "Polynomial":
        # c0 + c1 * x
        return Polynomial([c0, c1])

    def degree(self) -> int:
        if not self.coeffs:
            return -1
        return len(self.coeffs) - 1

    def _trim(self):
        # Прибираємо "зайві" майже нульові старші коефіцієнти
        while len(self.coeffs) > 1 and abs(self.coeffs[-1]) < 1e-14:
            self.coeffs.pop()

    def __add__(self, other: "Polynomial") -> "Polynomial":
        max_deg = max(self.degree(), other.degree())
        result = [0.0] * (max_deg + 1)
        for i in range(self.degree() + 1):
            result[i] += self.coeffs[i]
        for i in range(other.degree() + 1):
            result[i] += other.coeffs[i]
        return Polynomial(result)

    def __mul__(self, other):
        if isinstance(other, (int, float)):
            return Polynomial([c * other for c in self.coeffs])
        if isinstance(other, Polynomial):
            if self.degree() == -1 or other.degree() == -1:
                return Polynomial.constant(0.0)
            result_deg = self.degree() + other.degree()
            result = [0.0] * (result_deg + 1)
            for i, a in enumerate(self.coeffs):
                for j, b in enumerate(other.coeffs):
                    result[i + j] += a * b
            return Polynomial(result)
        raise TypeError("Unsupported multiplication type")

    __rmul__ = __mul__

    def evaluate(self, x: float) -> float:
        res = 0.0
        for c in reversed(self.coeffs):
            res = res * x + c
        return res

    def to_string(self, var: str = "x", precision: int = 6) -> str:
        """Рядкове представлення полінома."""
        parts = []
        for power in range(self.degree(), -1, -1):
            c = self.coeffs[power]
            if abs(c) < 1e-12:
                continue

            sign = "+" if c > 0 else "-"
            abs_c = abs(c)

            if not parts:
                # Перший доданок: знак лише якщо мінус
                prefix = "-" if c < 0 else ""
            else:
                prefix = f" {sign} "

            # Коефіцієнт
            if power == 0 or abs(abs_c - 1.0) > 1e-12:
                coeff_str = f"{abs_c:.{precision}f}"
            else:
                coeff_str = ""

            # Частина з змінною
            if power == 0:
                term = coeff_str
            elif power == 1:
                term = f"{coeff_str}{var}" if coeff_str else var
            else:
                term = f"{coeff_str}{var}^{power}" if coeff_str else f"{var}^{power}"

            parts.append(prefix + term)

        if not parts:
            return "0.0"
        return "".join(parts)


# ============================================
#  Клас інтерполятора Ньютона
# ============================================

class NewtonInterpolator:
    """
    Інтерполяція Ньютона на розділених різницях.
    x: вузли
    div_diff[i][j] = j-та розділена різниця, що починається з вузла i
    (F[0], F[1], ..., F[n-1] утворюють верхню діагональ,
     яка у програмі виводиться як верхній рядок).
    """

    def __init__(self, x: List[float], y: List[float]):
        if len(x) != len(y):
            raise ValueError("x та y повинні мати однакову довжину.")
        if len(x) < 2:
            raise ValueError("Потрібно щонайменше 2 вузли.")
        self.n = len(x)
        self.x = list(x)
        # Таблиця розділених різниць
        self.div_diff = [[0.0] * self.n for _ in range(self.n)]
        for i in range(self.n):
            self.div_diff[i][0] = y[i]
        self._compute_divided_differences()

    def _compute_divided_differences(self):
        for j in range(1, self.n):
            for i in range(self.n - j):
                denom = self.x[i + j] - self.x[i]
                if abs(denom) < 1e-14:
                    raise ZeroDivisionError("Ділення на нуль: дублюються значення x.")
                self.div_diff[i][j] = (self.div_diff[i + 1][j - 1] - self.div_diff[i][j - 1]) / denom

    def interpolate(self, val: float) -> float:
        """Обчислює значення полінома Ньютона в точці val (схема Горнера)."""
        result = self.div_diff[0][self.n - 1]
        for i in range(self.n - 2, -1, -1):
            result = self.div_diff[0][i] + (val - self.x[i]) * result
        return result

    def print_table(self, precision: int = 7):
        """
        Виводить повну таблицю розділених різниць:
        i | x[i] | F[0] ... F[n-1],
        причому верхня діагональ — це верхній рядок (i = 0).
        """
        n = self.n
        col_i = 3
        col_x = 14
        col_f = 12

        header = f"{'i':<{col_i}}{'x[i]':<{col_x}}"
        for j in range(n):
            header += f"{('F[' + str(j) + ']'):<{col_f}}"
        print(header)
        print("-" * len(header))

        for i in range(n):
            row = f"{i:<{col_i}}{self.x[i]:<{col_x}.{precision}f}"
            for j in range(n):
                if j <= n - 1 - i:
                    row += f"{self.div_diff[i][j]:<{col_f}.{precision}f}"
                else:
                    row += " " * col_f
            print(row)

    def newton_polynomial_string(self, var: str = "x", precision: int = 6) -> str:
        """
        Поліном у класичній формі Ньютона:
        P(x) = c0 + c1(x-x0) + c2(x-x0)(x-x1) + ...
        де c_k = F[0][k] — розділені різниці верхнього рядка.
        """
        s = f"P({var}) = {self.div_diff[0][0]:.{precision}f}"
        for k in range(1, self.n):
            coeff = self.div_diff[0][k]
            sign = "+" if coeff >= 0 else "-"
            s += f" {sign} {abs(coeff):.{precision}f}"
            for i in range(k):
                xi = self.x[i]
                inner_sign = "-" if xi >= 0 else "+"
                s += f"({var} {inner_sign} {abs(xi):.{precision}f})"
        return s

    def simplified_polynomial_string(self, var: str = "x", precision: int = 6) -> str:
        """Повертає степеневу форму полінома (розкриті дужки)."""
        P = Polynomial.constant(0.0)
        term_product = Polynomial.constant(1.0)

        for k in range(self.n):
            ck = self.div_diff[0][k]
            if k == 0:
                current_term = Polynomial.constant(ck)
            else:
                term_product = term_product * Polynomial.linear(-self.x[k - 1], 1.0)
                current_term = term_product * ck
            P = P + current_term

        return f"P({var}) = {P.to_string(var, precision)}"

    def calculate_plot_points(self, start: float, end: float, num_points: int = 500) -> List[Tuple[float, float]]:
        """Генерує точки (arg, P(arg)) на відрізку [start; end] для побудови графіка."""
        if num_points < 2:
            num_points = 2
        step = (end - start) / (num_points - 1)
        pts = []
        for i in range(num_points):
            xi = start + i * step
            pts.append((xi, self.interpolate(xi)))
        return pts


# ============================================
#  Допоміжні функції
# ============================================

def f(x: float) -> float:
    """Аналітична функція для прямої інтерполяції."""
    return math.tan(x)


def is_monotone_strict(seq: List[float]) -> bool:
    """Перевірка строгої монотонності."""
    inc = all(seq[i] < seq[i + 1] for i in range(len(seq) - 1))
    dec = all(seq[i] > seq[i + 1] for i in range(len(seq) - 1))
    return inc or dec


def generate_nodes(a: float = -0.5, b: float = 0.5, n_points: int = 15):
    """15 рівновіддалених вузлів на [a, b] для tg(x)."""
    n = n_points - 1
    h = (b - a) / n
    xs = [a + i * h for i in range(n_points)]
    ys = [f(x) for x in xs]
    return xs, ys


def write_dat(filename: str, data: List[Tuple[float, float]]):
    """Записує дані у .dat файл для подальшої побудови графіка (gnuplot, Excel, тощо)."""
    with open(filename, "w", encoding="utf-8") as f_out:
        for x, y in data:
            f_out.write(f"{x:.10f} {y:.10f}\n")


# ============================================
#  Головна логіка
# ============================================

def main():
    # 1) Генеруємо вузли
    xs, ys = generate_nodes()

    print("\n=== Вузли інтерполяції для f(x) = tg(x) на відрізку [-0.5; 0.5] ===")
    print(f"{'i':>3} {'x_i':>12} {'f(x_i)':>18}")
    for i, (xv, yv) in enumerate(zip(xs, ys)):
        print(f"{i:>3} {xv:>12.6f} {yv:>18.10f}")

    # 2) Пряма інтерполяція
    interp = NewtonInterpolator(xs, ys)

    print("\n=== Таблиця розділених різниць (вхід: x, вихід: y) ===")
    interp.print_table(precision=7)

    print("\n=== Поліном у формі Ньютона (неспростений) ===")
    print(interp.newton_polynomial_string(var="x", precision=6))

    print("\n=== Поліном у степеневій формі (спрощений) ===")
    print(interp.simplified_polynomial_string(var="x", precision=6))

    # 3) Перевірка точності в кількох точках
    print("\n=== Перевірка точності інтерполяції у контрольних точках ===")
    test_points = [-0.5, -0.25, 0.0, 0.25, 0.5]
    print(f"{'x':>10} {'f(x)':>18} {'P(x)':>18} {'|f(x)-P(x)|':>18}")
    for xv in test_points:
        fx = f(xv)
        px = interp.interpolate(xv)
        err = abs(fx - px)
        print(f"{xv:>10.4f} {fx:>18.10f} {px:>18.10f} {err:>18.10e}")

    # 4) Дані для графіків f(x) та P(x)
    plot_start, plot_end = xs[0], xs[-1]
    xs_plot = [plot_start + i * (plot_end - plot_start) / 499 for i in range(500)]
    original_data = [(x, f(x)) for x in xs_plot]
    poly_data = [(x, interp.interpolate(x)) for x in xs_plot]

    write_dat("original_tan_plot.dat", original_data)
    write_dat("interp_poly_plot.dat", poly_data)
    print("\nФайли original_tan_plot.dat та interp_poly_plot.dat створено для побудови графіків.")

    # --- ГРАФІК:f(x) та P(x) ---
    plt.figure()
    plt.plot(xs_plot, [f(x) for x in xs_plot], label="f(x) = tg(x)")
    plt.plot(xs_plot, [interp.interpolate(x) for x in xs_plot], label="P(x) – поліном Ньютона")
    plt.scatter(xs, ys, marker="o", label="вузли інтерполяції")
    plt.xlabel("x")
    plt.ylabel("y")
    plt.title("Пряма інтерполяція: f(x) та P(x)")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.savefig("direct_interpolation_tan_vs_poly.png", dpi=300)

    # 5) Обернена інтерполяція
    print("\n=== Обернена інтерполяція Q(y) = x ===")
    print("Перевірка монотонності послідовності y_i = tg(x_i):")
    if not is_monotone_strict(ys):
        print("  ⚠ y_i не є строго монотонною, обернена інтерполяція некоректна.")
        return
    else:
        print("  ▶ y_i є строго монотонною. Можна виконувати обернену інтерполяцію.\n")

    # Міняємо місцями (y, x), сортуємо за y
    pairs = sorted(zip(ys, xs), key=lambda p: p[0])
    ys_sorted = [p[0] for p in pairs]
    xs_sorted = [p[1] for p in pairs]

    inv_interp = NewtonInterpolator(ys_sorted, xs_sorted)

    print("=== Таблиця розділених різниць (вхід: y, вихід: x) ===")
    inv_interp.print_table(precision=7)

    print("\n=== Поліном Q(y) у степеневій формі (наближає arctan(y)) ===")
    print(inv_interp.simplified_polynomial_string(var="y", precision=6))

    # Тест для y* = 0.3
    y_star = 0.3
    x_interp = inv_interp.interpolate(y_star)
    x_true = math.atan(y_star)
    err_inv = abs(x_true - x_interp)

    print("\nПеревірка для y* = 0.3:")
    print(f"x_true = arctan(0.3) = {x_true:.10f}")
    print(f"x_interp (з оберненої інтерполяції) = {x_interp:.10f}")
    print(f"|x_true - x_interp| = {err_inv:.10e}")

    # Дані для графіків Q(y) та arctan(y)
    y_min, y_max = ys_sorted[0], ys_sorted[-1]
    ys_plot = [y_min + i * (y_max - y_min) / 499 for i in range(500)]
    inv_poly_data = [(y, inv_interp.interpolate(y)) for y in ys_plot]
    inv_true_data = [(y, math.atan(y)) for y in ys_plot]

    write_dat("inverse_interp_poly_y_x.dat", inv_poly_data)
    write_dat("inverse_true_arctan_y_x.dat", inv_true_data)
    print("\nФайли inverse_interp_poly_y_x.dat та inverse_true_arctan_y_x.dat створено для побудови графіків Q(y) та arctan(y).")

    # --- ГРАФІК: Q(y) та arctan(y) ---
    plt.figure()
    plt.plot(ys_plot, [math.atan(y) for y in ys_plot], label="x = arctan(y)")
    plt.plot(ys_plot, [inv_interp.interpolate(y) for y in ys_plot], label="Q(y) – обернена інтерполяція")
    plt.scatter(ys_sorted, xs_sorted, marker="o", label="обернені вузли (y_i, x_i)")
    plt.xlabel("y")
    plt.ylabel("x")
    plt.title("Обернена інтерполяція: Q(y) та arctan(y)")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.savefig("inverse_interpolation_arctan_vs_Q.png", dpi=300)


if __name__ == "__main__":
    main()

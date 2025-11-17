import numpy as np

# --- Параметри ---
interval_start, interval_end = 0.8, 1.2  # [a,b]
initial_guess = 0.8  # x0
tolerance = 1e-4  # ε
max_iterations = 100


# --- Функція та перша похідна ---
def target_function(x):
    """f(x) = x^4 + x^3 - 6x^2 + 20x - 16"""
    return x ** 4 + x ** 3 - 6 * x ** 2 + 20 * x - 16


def target_function_derivative(x):
    """f'(x)"""
    return 4 * x ** 3 + 3 * x ** 2 - 12 * x + 20


# --- Метод простої ітерації: φ(x) = x - (x/20)f(x) ---
def phi_simple_iteration(x):
    """Ітераційна функція φ(x)"""
    return x - (x / 20.0) * target_function(x)


def phi_simple_iteration_derivative(x):
    """Похідна ітераційної функції φ'(x)"""
    return 1.0 - target_function(x) / 20.0 - (x / 20.0) * target_function_derivative(x)


# --- Службові функції ---
def max_abs_on_interval(func, a, b, n=10001):
    xs = np.linspace(a, b, n)
    return float(np.abs(func(xs)).max())


def check_convergence_simple(phi, dphi, x0, a, b):
    """Перевірка 2-х умов збіжності для методу простої ітерації"""
    delta = max(abs(a - x0), abs(b - x0))
    q = max_abs_on_interval(dphi, a, b)
    condition2_left = abs(phi(x0) - x0)
    condition2_right = (1 - q) * delta
    is_convergent = (q < 1 and condition2_left <= condition2_right)
    return q, delta, condition2_left, condition2_right, is_convergent


def iterate_fixed_point(phi, x0, eps, q, nmax=max_iterations):
    values = [x0]

    # Визначаємо правильну умову зупинки залежно від q
    if q < 0.5:
        stop_condition = lambda diff: diff <= (1 - q) / q * eps
        print(f"Умова зупинки: |Δ| <= (1-q)/q * ε ≈ {(1 - q) / q * eps:.2e}")
    else:
        stop_condition = lambda diff: diff <= eps
        print(f"Умова зупинки: |Δ| <= ε = {eps:.2e}")

    for _ in range(nmax):
        x_next = phi(values[-1])
        values.append(x_next)
        difference = abs(values[-1] - values[-2])
        if stop_condition(difference):
            break
    return values


def print_iterations_table(values, title):
    print(title)
    print(f"{'n':>3} | {'x_n':>14} | {'Δ = |x_n - x_{n-1}|':>20}")
    print("-" * 45)
    for i, x in enumerate(values):
        if i == 0:
            print(f"{i:>3} | {x:>14.10f} | {'-':>20}")
        else:
            delta = abs(values[i] - values[i - 1])
            print(f"{i:>3} | {x:>14.10f} | {delta:>20.10f}")
    print(f"Зупинка на кроці n={len(values) - 1}, x ≈ {values[-1]:.10f}\n")


# --- 1) МЕТОД ПРОСТОЇ ІТЕРАЦІЇ ---
q, delta, left, right, ok = check_convergence_simple(
    phi_simple_iteration, phi_simple_iteration_derivative,
    initial_guess, interval_start, interval_end
)
print("=== Метод простої ітерації (Ψ(x)=-x/20) ===")
print(f"S=[{interval_start},{interval_end}], x0={initial_guess}, δ={delta}")
print(f"q = max|φ'(x)| ≈ {q:.6f}  (<1 ? {'так' if q < 1 else 'ні'})")
print(f"|φ(x0)-x0| = {left:.6f}  ≤  (1-q)δ = {right:.6f}  --> {'виконується' if ok else 'НЕ виконується'}\n")

# <--- (передаємо q в функцію ітерацій)
values_simple = iterate_fixed_point(phi_simple_iteration, initial_guess, tolerance, q)
print_iterations_table(values_simple, "Таблиця ітерацій (проста ітерація)")

# --- 2) МЕТОД РЕЛАКСАЦІЇ: x_{n+1} = x_n - τ f(x_n) ---
xs = np.linspace(interval_start, interval_end, 20001)
abs_fp = np.abs(target_function_derivative(xs))
m1 = float(abs_fp.min())
M1 = float(abs_fp.max())
tau_opt = 2.0 / (M1 + m1)
q_relax = (M1 - m1) / (M1 + m1)


def iterate_relaxation(x0, eps, nmax=max_iterations, tau=tau_opt):
    values = [x0]
    for _ in range(nmax):
        x_next = values[-1] - tau * target_function(values[-1])
        values.append(x_next)
        if abs(values[-1] - values[-2]) <= eps:
            break
    return values


print("=== Метод релаксації ===")
print(f"m1 = min|f'(x)| ≈ {m1:.6f},  M1 = max|f'(x)| ≈ {M1:.6f}")
print(f"τ_opt = 2/(M1+m1) ≈ {tau_opt:.6f},  q0 = (M1-m1)/(M1+m1) ≈ {q_relax:.6f}\n")
print(f"Умова зупинки: |Δ| <= ε = {tolerance:.2e}")

values_relax = iterate_relaxation(initial_guess, tolerance)
print_iterations_table(values_relax, "Таблиця ітерацій (релаксація)")

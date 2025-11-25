import numpy as np

np.set_printoptions(precision=6, suppress=True)

# -----------------------------------------
# Функція перевірки A = A^T > 0
# -----------------------------------------
def check_positive_definite(A):
    print("\nПеревірка умови A = A^T > 0:")

    # 1) Перевірка симетрії
    if not np.allclose(A, A.T):
        print(" ❌ Матриця НЕ симетрична → степеневий метод не можна застосовувати.")
        return False
    print(" ✔ Матриця симетрична (A = A^T)")

    # 2) Перевірка додатної визначеності через головні мінори
    n = A.shape[0]
    print("Перевірка додатної визначеності (головні мінори):")
    for i in range(1, n + 1):
        minor = np.linalg.det(A[:i, :i])
        print(f"  |A_{i}| = {minor:.6f}")
        if minor <= 0:
            print("Один з мінорів ≤ 0 → A не є додатно визначеною.")
            return False

    print("Усі головні мінори додатні → A > 0")
    return True


# -----------------------------------------
# 1. МЕТОД СКАЛЯРНИХ ДОБУТКІВ
# -----------------------------------------
def scalar_products_method(A, x0, eps=1e-4, max_iter=1000):

    print("\n===== МЕТОД СКАЛЯРНИХ ДОБУТКІВ =====")
    xk = x0.astype(float)
    lambda_prev = 0.0

    for k in range(1, max_iter + 1):
        print(f"\n--- Ітерація {k} ---")
        print("x(k) =", np.round(xk, 6))

        x_next = A @ xk
        print("A * x(k) =", np.round(x_next, 6))

        num = np.dot(x_next, xk)
        den = np.dot(xk, xk)

        lambda_next = num / den
        print(f"λ(k+1) = {lambda_next:.6f}")

        if k > 1:
            diff = abs(lambda_next - lambda_prev)
            print(f"|λ(k+1) - λ(k)| = {diff:.6f}")

            if diff <= eps:
                print(" → Критерій зупинки виконано.")
                eigenvector = x_next / np.linalg.norm(x_next)
                return lambda_next, eigenvector, k

        lambda_prev = lambda_next
        xk = x_next

    eigenvector = xk / np.linalg.norm(xk)
    return lambda_prev, eigenvector, max_iter


# -----------------------------------------
# 2. НОРМАЛІЗОВАНИЙ МЕТОД СКАЛЯРНИХ ДОБУТКІВ
# -----------------------------------------
def scalar_products_normalized(A, x0, eps=1e-9, max_iter=1000):

    print("\n===== НОРМАЛІЗОВАНИЙ МЕТОД СКАЛЯРНИХ ДОБУТКІВ =====")
    xk = x0.astype(float)
    lambda_prev = 0.0

    for k in range(1, max_iter + 1):
        print(f"\n--- Ітерація {k} ---")
        print("x(k) =", np.round(xk, 6))

        norm_xk = np.linalg.norm(xk)
        ek = xk / norm_xk
        print("e(k) =", np.round(ek, 6))

        x_next = A @ ek
        print("A * e(k) =", np.round(x_next, 6))

        lambda_next = np.dot(x_next, ek)
        print(f"λ(k+1) = {lambda_next:.6f}")

        if k > 1:
            diff = abs(lambda_next - lambda_prev)
            print(f"|λ(k+1) - λ(k)| = {diff:.6f}")

            if diff <= eps:
                print(" → Критерій зупинки виконано.")
                return lambda_next, ek, k

        lambda_prev = lambda_next
        xk = x_next

    eigenvector = ek
    return lambda_prev, eigenvector, max_iter


# -----------------------------------------
# 3. СТЕПЕНЕВИЙ МЕТОД (повністю як у методичці)
# -----------------------------------------
def power_method(A, x0, eps=1e-4, max_iter=1000):

    print("\n===== СТЕПЕНЕВИЙ МЕТОД =====")

    # ДОДАНО: умова A = A^T > 0
    if not check_positive_definite(A):
        return None, None, 0

    xk = x0.astype(float)
    lambda_prev = 0.0

    for k in range(1, max_iter + 1):
        print(f"\n--- Ітерація {k} ---")
        print("x(k) =", np.round(xk, 6))

        y = A @ xk
        print("A * x(k) =", np.round(y, 6))

        m = np.argmax(np.abs(y))
        lambda_next = y[m] / xk[m]
        print(f"λ(k+1) = y[{m}] / x[{m}] = {lambda_next:.6f}")

        x_next = y / lambda_next
        print("x(k+1) =", np.round(x_next, 6))

        if k > 1:
            diff = abs(lambda_next - lambda_prev)
            print(f"|λ(k+1) - λ(k)| = {diff:.6f}")

            if diff <= eps:
                print(" → Критерій зупинки виконано.")
                eigenvector = x_next / np.linalg.norm(x_next)
                return lambda_next, eigenvector, k

        lambda_prev = lambda_next
        xk = x_next

    eigenvector = xk / np.linalg.norm(xk)
    return lambda_prev, eigenvector, max_iter


# -----------------------------------------
# ТЕСТОВИЙ ЗАПУСК
# -----------------------------------------
if __name__ == "__main__":

    A = np.array([
        [6, 2, 1, 0, 0],
        [2, 7, 2, 1, 0],
        [1, 2, 8, 2, 1],
        [0, 1, 2, 7, 2],
        [0, 0, 1, 2, 6]
    ], dtype=float)

    x0 = np.ones(5)

    print("Матриця A:")
    print(A)

    lam1, v1, it1 = scalar_products_method(A, x0)
    print("\nРезультат методу скалярних добутків:")
    print("λ =", lam1)
    print("v =", v1)

    lam2, v2, it2 = scalar_products_normalized(A, x0)
    print("\nРезультат нормалізованого методу:")
    print("λ =", lam2)
    print("v =", v2)

    lam3, v3, it3 = power_method(A, x0)
    print("\nРезультат степеневого методу:")
    print("λ =", lam3)
    print("v =", v3)

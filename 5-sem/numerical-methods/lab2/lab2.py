import numpy as np

# -------------------------------
# Генерація тридіагональної діагонально домінантної матриці
# -------------------------------

def generate_tridiagonal_dd_matrix(n=4, seed=40):
    """
    Генерує тридіагональну діагонально домінантну матрицю A розміру n x n 
    з цілими елементами |a_ij| < 10.
    
    Повертає: A, a (піддіагональ), c (діагональ), b (наддіагональ)
    """
    rng = np.random.default_rng(seed)

    # піддіагональ та наддіагональ беремо з {-3,-2,-1,1,2,3}
    a = np.zeros(n, dtype=int)  # a[0] не використовується
    b = np.zeros(n, dtype=int)  # b[-1] не використовується

    for i in range(1, n):
        a[i] = rng.integers(-3, 4)
        while a[i] == 0:
            a[i] = rng.integers(-3, 4)

    for i in range(n - 1):
        b[i] = rng.integers(-3, 4)
        while b[i] == 0:
            b[i] = rng.integers(-3, 4)

    # головна діагональ c: забезпечуємо строгу діагональну домінантність
    c = np.zeros(n, dtype=int)
    for i in range(n):
        sum_off = 0
        if i > 0:
            sum_off += abs(a[i])
        if i < n - 1:
            sum_off += abs(b[i])

        extra = rng.integers(1, 4)  # 1..3
        c[i] = sum_off + extra      # гарантуємо |c[i]| < 10

    # будуємо повну матрицю A
    A = np.zeros((n, n), dtype=int)
    for i in range(n):
        A[i, i] = c[i]
        if i > 0:
            A[i, i - 1] = a[i]
        if i < n - 1:
            A[i, i + 1] = b[i]

    return A, a, c, b


# -------------------------------
# Метод Гаусса з вибором головного елемента за всією матрицею
# -------------------------------

def gauss_complete_pivot(A, b, tol=1e-12):
    """
    Метод Гаусса з повним вибором головного елемента.
    Повертає розв'язок x.
    """
    A = A.astype(float).copy()
    b = b.astype(float).copy()
    n = A.shape[0]

    col_perm = np.arange(n)

    # Прямий хід
    for k in range(n):
        # Пошук максимального елемента в підматриці k:n
        sub = np.abs(A[k:, k:])
        p_rel, q_rel = np.unravel_index(np.argmax(sub), sub.shape)
        p, q = p_rel + k, q_rel + k

        # Перестановка рядків
        if p != k:
            A[[k, p], :] = A[[p, k], :]
            b[k], b[p] = b[p], b[k]

        # Перестановка стовпців
        if q != k:
            A[:, [k, q]] = A[:, [q, k]]
            col_perm[k], col_perm[q] = col_perm[q], col_perm[k]

        pivot = A[k, k]
        if abs(pivot) < tol:
            raise ValueError(f"Нульовий головний елемент на кроці {k+1}")

        # Елімінація
        for i in range(k + 1, n):
            factor = A[i, k] / pivot
            A[i, k:] -= factor * A[k, k:]
            b[i] -= factor * b[k]

    # Зворотний хід
    y = np.zeros(n)
    for i in range(n - 1, -1, -1):
        y[i] = (b[i] - np.dot(A[i, i + 1:], y[i + 1:])) / A[i, i]

    # Відновлення порядку змінних
    x = np.zeros(n)
    x[col_perm] = y
    return x


# -------------------------------
# Метод прогонки (Томаса)
# -------------------------------

def thomas_method(a, c, b, d):
    """
    Метод прогонки для тридіагональної системи.
    
    Параметри:
    a - піддіагональ (a[0] не використовується)
    c - головна діагональ
    b - наддіагональ (b[-1] не використовується)
    d - вектор правої частини
    
    Повертає: розв'язок x
    """
    n = len(c)
    a = a.astype(float).copy()
    b = b.astype(float).copy()
    c = c.astype(float).copy()
    d = d.astype(float).copy()

    # Прямий хід: модифіковані коефіцієнти
    cp = np.zeros(n)
    dp = np.zeros(n)

    cp[0] = c[0]
    dp[0] = d[0]

    for i in range(1, n):
        m = a[i] / cp[i - 1]
        cp[i] = c[i] - m * b[i - 1]
        dp[i] = d[i] - m * dp[i - 1]
        
        if abs(cp[i]) < 1e-12:
            raise ValueError(f"Метод прогонки нестійкий на кроці {i}")

    # Зворотний хід
    x = np.zeros(n)
    x[-1] = dp[-1] / cp[-1]
    for i in range(n - 2, -1, -1):
        x[i] = (dp[i] - b[i] * x[i + 1]) / cp[i]

    return x


# -------------------------------
# Метод Зейделя
# -------------------------------

def gauss_seidel(A, b, eps=1e-6, max_iter=10_000):
    """
    Метод Зейделя для Ax = b.
    
    Повертає: (x, k), де k - кількість ітерацій
    """
    A = A.astype(float)
    b = b.astype(float)
    n = A.shape[0]

    x = np.zeros(n)
    
    print("\nІтераційний процес:")
    print("-" * 80)
    
    for k in range(1, max_iter + 1):
        x_new = x.copy()
        
        for i in range(n):
            # Сума з новими значеннями (0..i-1)
            s1 = np.dot(A[i, :i], x_new[:i])
            # Сума зі старими значеннями (i+1..n-1)
            s2 = np.dot(A[i, i + 1:], x[i + 1:])
            
            x_new[i] = (b[i] - s1 - s2) / A[i, i]

        # Обчислення відхилення
        diff = np.linalg.norm(x_new - x, ord=np.inf)
        
        # Виведення результату ітерації
        x_str = ", ".join([f"{val:10.6f}" for val in x_new])
        print(f"Ітерація {k:3d}: x = [{x_str}]  ||Δx|| = {diff:.3e}", end="")
        
        # Перевірка збіжності
        if diff < eps:
            print("  ✓ Збіжність досягнута!")
            print("-" * 80)
            return x_new, k
        else:
            print(f"  (> {eps:.0e})")
        
        x = x_new

    print(f"\n⚠ Досягнуто максимум ітерацій ({max_iter})")
    print("-" * 80)
    return x, max_iter


# -------------------------------
# Допоміжні функції
# -------------------------------

def check_diagonal_dominance(A):
    """Перевірка діагональної домінантності"""
    n = A.shape[0]
    print("\nПеревірка діагональної домінантності:")
    print("-" * 60)
    
    is_dominant = True
    for i in range(n):
        diag = abs(A[i, i])
        sum_off = np.sum(np.abs(A[i, :])) - diag
        dominant = diag >= sum_off
        is_dominant = is_dominant and dominant
        
        status = "✓" if dominant else "✗"
        print(f"Рядок {i+1}: |a{i+1}{i+1}| = {diag:5.1f}  {'≥' if dominant else '<'}  "
              f"{sum_off:5.1f} = Σ|aᵢⱼ|  {status}")
    
    return is_dominant


def save_to_file(A, b, filename="matrix_and_b.txt"):
    """Збереження матриці та вектора у файл"""
    with open(filename, "w", encoding="utf-8") as f:
        f.write("Матриця A:\n")
        for row in A:
            f.write(" ".join(f"{val:4d}" for val in row) + "\n")
        f.write("\nВектор b:\n")
        f.write(" ".join(f"{val:4d}" for val in b) + "\n")


# -------------------------------
# Головна програма
# -------------------------------

def main():
    # Генерація матриці та вектора
    n = 4
    A, subdiag, diag, superdiag = generate_tridiagonal_dd_matrix(n=n, seed=40)
    
    rng = np.random.default_rng(123)
    b = rng.integers(-9, 10, size=n)

    print("\nМатриця A (тридіагональна, діагонально домінантна):")
    print(A)
    print("\nВектор b:")
    print(b)

    # Збереження у файл (без повідомлення)
    save_to_file(A, b)

    # Перевірка діагональної домінантності
    is_dd = check_diagonal_dominance(A)
    
    if not is_dd:
        print("\n⚠ УВАГА: Матриця НЕ є діагонально домінантною!")

    # Перевірка визначника
    det_A = np.linalg.det(A.astype(float))
    print(f"\nВизначник: det(A) = {det_A:.6f}")
    
    if abs(det_A) < 1e-12:
        print("⚠ Система вироджена!")
        return

    # Введення точності для методу Зейделя
    print("\n" + "=" * 70)
    eps = float(input("Введіть точність ε для методу Зейделя (наприклад, 1e-6): "))

    # ========== МЕТОД ГАУССА ==========
    print("\n" + "=" * 70)
    print("1. МЕТОД ГАУССА (з вибором головного елемента)")
    print("=" * 70)
    
    x_gauss = gauss_complete_pivot(A, b)
    
    print("Розв'язок:")
    for i, val in enumerate(x_gauss):
        print(f"  x{i+1} = {val:12.8f}")

    # ========== МЕТОД ПРОГОНКИ ==========
    print("\n" + "=" * 70)
    print("2. МЕТОД ПРОГОНКИ")
    print("=" * 70)
    
    x_thomas = thomas_method(subdiag, diag, superdiag, b)
    
    print("Розв'язок:")
    for i, val in enumerate(x_thomas):
        print(f"  x{i+1} = {val:12.8f}")

    # ========== МЕТОД ЗЕЙДЕЛЯ ==========
    print("\n" + "=" * 70)
    print("3. МЕТОД ЗЕЙДЕЛЯ")
    print("=" * 70)
    
    x_seidel, iters = gauss_seidel(A, b, eps=eps)
    
    print(f"Збіжність досягнута за {iters} ітерацій")
    print("\nРозв'язок:")
    for i, val in enumerate(x_seidel):
        print(f"  x{i+1} = {val:12.8f}")

    # ========== ПОРІВНЯННЯ РЕЗУЛЬТАТІВ ==========
    print("\n" + "=" * 70)
    print("ПОРІВНЯННЯ РЕЗУЛЬТАТІВ")
    print("=" * 70)
    
    print("\nВідхилення між методами:")
    print(f"  ||x_Гаусс - x_Прогонка||    = {np.linalg.norm(x_gauss - x_thomas):.3e}")
    print(f"  ||x_Гаусс - x_Зейдель||     = {np.linalg.norm(x_gauss - x_seidel):.3e}")
    print(f"  ||x_Прогонка - x_Зейдель|| = {np.linalg.norm(x_thomas - x_seidel):.3e}")

    # Перевірка через NumPy
    print("\n" + "=" * 70)
    print("ПЕРЕВІРКА (NumPy)")
    print("=" * 70)
    
    x_numpy = np.linalg.solve(A.astype(float), b.astype(float))
    
    print("Розв'язок:")
    for i, val in enumerate(x_numpy):
        print(f"  x{i+1} = {val:12.8f}")
    
    print(f"\nВідхилення від NumPy:")
    print(f"  ||x_Гаусс - x_NumPy||    = {np.linalg.norm(x_gauss - x_numpy):.3e}")
    print(f"  ||x_Прогонка - x_NumPy|| = {np.linalg.norm(x_thomas - x_numpy):.3e}")
    print(f"  ||x_Зейдель - x_NumPy||  = {np.linalg.norm(x_seidel - x_numpy):.3e}")

    print("\n" + "=" * 70)
    print("✅ Розв'язання завершено успішно!")
    print("=" * 70)


if __name__ == "__main__":
    main()
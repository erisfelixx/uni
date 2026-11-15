# Лабораторна робота 5. Модель Леонтьєва, модель цін. Варіант 12
# Задача 12.2: аналіз технологічної матриці A (числа та вектори Фробеніуса, продуктивність, матриця повних витрат, збіжність ряду, кінцевий випуск)
import numpy as np
import matplotlib.pyplot as plt

np.set_printoptions(precision=4, suppress=True)


print("=" * 25, "ЗАДАЧА 12.2", "=" * 25)

A = np.array([[0.65, 0.10, 0.25],
              [0.35, 0.35, 0.20],
              [0.10, 0.45, 0.10]])
E = np.eye(3)
print("Матриця A:\n", A)

# Характеристичний поліном det(lambda·E - A) = lambda^3 + c1·lambda^2 + c2·lambda + c3
coef = np.poly(A)
print("\nКоефіцієнти характеристичного полінома:", coef)
print(f"Поліном: lambda^3 {coef[1]:+.4f}·lambda^2 {coef[2]:+.4f}·lambda {coef[3]:+.6f}")

# Власні числа та власні вектори
lam, vec = np.linalg.eig(A)
print("\nВласні числа:", lam.real)

# Число Фробеніуса – найбільше власне число
k = np.argmax(lam.real)
lambdaA = lam[k].real
print(f"Число Фробеніуса: lambdaA = {lambdaA:.4f}")

# Правий вектор Фробеніуса (повний випуск): власний вектор для lambdaA.
# Вектор визначений з точністю до множника (і знака), тому беремо модуль і нормуємо відносно найменшого значення.
x1v = np.abs(vec[:, k].real)
xA = x1v / x1v.min()
print("Правий вектор Фробеніуса (нормований):", xA)

# Лівий вектор Фробеніуса (ціни): p = pA  <=>  A^T·p^T = p^T, тобто власний вектор транспонованої матриці
lam1, vec1 = np.linalg.eig(A.T)
k1 = np.argmax(lam1.real)
print(f"Число Фробеніуса матриці A^T: {lam1[k1].real:.4f}")
p1 = np.abs(vec1[:, k1].real)
pA = p1 / p1.min()
print("Лівий вектор Фробеніуса (нормований):", pA)

# Продуктивність
if lambdaA < 1:
    print(f"\nlambdaA = {lambdaA:.4f} < 1, отже матриця A продуктивна")
else:
    print(f"\nlambdaA = {lambdaA:.4f} >= 1, отже матриця A не є продуктивною")

# Матриця повних витрат
B = np.linalg.inv(E - A)
print("\nМатриця повних витрат B = (E - A)^(-1):\n", B)

# Збіжність ряду E + A + A^2 + ... + A^N до B (критерій: різниця < 0.01)
S = E.copy()          # часткова сума ряду
An = E.copy()         # поточний степінь A
N = 0
deviations = [np.abs(B - S).max()]
while np.abs(B - S).max() >= 0.01:
    N += 1
    An = An @ A       # A^N
    S = S + An
    deviations.append(np.abs(B - S).max())
print(f"\nРяд збігається: при N = {N} max|B - S_N| = {deviations[-1]:.6f} < 0.01")
print("Сума ряду S_N:\n", S)

# Вектор кінцевого випуску
y = np.array([900, 1500, 1000])
xx = B @ y
print(f"\nКінцеве споживання y = {y}")
print("Вектор кінцевого (повного) випуску x = B·y =", xx)

# Графік збіжності ряду
plt.figure(figsize=(8, 5))
plt.semilogy(range(N + 1), deviations, "o-", ms=3)
plt.axhline(0.01, color="red", ls="--", label="критерій 0.01")
plt.xlabel("N (кількість доданків A^N)")
plt.ylabel("max |B − (E + A + ... + A^N)|")
plt.title("Збіжність ряду E + A + A² + ... + A^N до B")
plt.legend(); plt.grid(alpha=.3, which="both")
plt.savefig("lab5_convergence.png", dpi=130, bbox_inches="tight")
plt.show()
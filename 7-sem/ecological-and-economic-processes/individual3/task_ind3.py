# Самостійна робота 3: варіант 12
# Пункт 1: аналітичний вигляд функцій попиту та пропозиції
# Пункт 2: точка ринкової рівноваги, графік в осях (Q, P), стабільність
# Пункт 3: зміна рівноваги після введення субсидії для виробника (sub = 1)
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import brentq, fsolve

# --- Вихідні дані ---
Price  = np.array([1.8, 2.3, 3.2, 3.7, 4.3, 4.9, 5.5, 6.2])
Demand = np.array([130, 97, 68, 56, 44, 36, 30, 24])
Supply = np.array([20, 40, 65, 75, 83, 90, 95, 100])
sub = 1                                               # субсидія для виробника

p = np.linspace(Price.min(), Price.max(), 200)        # сітка цін для гладких графіків



# === ПУНКТ 1 ===

print("=" * 25, "ПУНКТ 1", "=" * 25)

def r2(y, f):
    """Коефіцієнт детермінації R^2"""
    return 1 - np.sum((y - f)**2) / np.sum((y - np.mean(y))**2)

def trendlines(P, Q):
    """Лінії тренду, як в Excel (метод найменших квадратів).
    Експоненційна та степенева будуються через логарифм Q, тому їх R^2
    рахується для ln(Q) – так само, як це робить Excel."""
    res = {}
    b, a = np.polyfit(P, Q, 1)
    res["лінійна       Q = a + b*P"]      = (a, b, r2(Q, a + b*P))
    b, a = np.polyfit(P, np.log(Q), 1)
    res["експоненційна Q = a*e^(b*P)"]    = (np.exp(a), b, r2(np.log(Q), a + b*P))
    b, a = np.polyfit(np.log(P), Q, 1)
    res["логарифмічна  Q = a*ln(P) + b"]  = (b, a, r2(Q, a + b*np.log(P)))
    b, a = np.polyfit(np.log(P), np.log(Q), 1)
    res["степенева     Q = a*P^b"]        = (np.exp(a), b, r2(np.log(Q), a + b*np.log(P)))
    return res

for name, Q in [("ПОПИТ (Demand)", Demand), ("ПРОПОЗИЦІЯ (Supply)", Supply)]:
    print(f"\n{name}")
    for kind, (a, b, R2) in trendlines(Price, Q).items():
        print(f"  {kind:32s} a = {a:9.4f}   b = {b:8.4f}   R^2 = {R2:.4f}")

# Обрані функції (найбільший R^2), коефіцієнти округлено
# Попит:      Q_d = 235.56 * e^(-0.378 P),   R^2 = 0.9926
# Пропозиція: Q_s = 65.031 * ln(P) - 14.104, R^2 = 0.9865
def Func_dem(P): return 235.56*np.exp(-0.378*P)
def Func_sup(P): return 65.031*np.log(P) - 14.104

print("\nPrice   Demand  Func_dem   Supply  Func_sup")
for pr, d, s in zip(Price, Demand, Supply):
    print(f"{pr:5.1f} {d:8.0f} {Func_dem(pr):9.3f} {s:8.0f} {Func_sup(pr):9.3f}")

# Графік 1: дані спостережень та лінії тренду (вісь X – ціна, вісь Y – кількість)
plt.figure(figsize=(8, 5))
plt.plot(Price, Demand, "o-", color="tab:blue", label="Demand")
plt.plot(Price, Supply, "s-", color="tab:red", label="Supply")
plt.plot(p, Func_dem(p), ":", color="tab:blue", lw=2,
         label="Експоненційна (Demand): y = 235.56e^(-0.378x), R² = 0.9926")
plt.plot(p, Func_sup(p), ":", color="tab:red", lw=2,
         label="Логарифмічна (Supply): y = 65.031ln(x) - 14.104, R² = 0.9865")
plt.xlabel("Price"); plt.ylabel("Q")
plt.title("Дані спостережень та лінії тренду")
plt.legend(fontsize=8); plt.grid(alpha=.3)
plt.savefig("punkt1_trend.png", dpi=130, bbox_inches="tight")


# === ПУНКТ 2 ===
print("\n" + "=" * 25, "ПУНКТ 2", "=" * 25)

# Точка рівноваги: Q_d(P) - Q_s(P) = 0
# Спосіб 1: пошук кореня на відрізку
P_star = brentq(lambda P: Func_dem(P) - Func_sup(P), Price.min(), Price.max())
print("Підбір параметра:")
print(f"  Q*d = {Func_dem(P_star):.4f}   Q*s = {Func_sup(P_star):.4f}   P* = {P_star:.4f}"
      f"   Q*d - Q*s = {Func_dem(P_star) - Func_sup(P_star):.2e}")

# Спосіб 2: розв'язання нелінійного рівняння
P_solver = fsolve(lambda P: Func_dem(P) - Func_sup(P), x0=1.0)[0]
print("Пошук рішення (Solver):")
print(f"  Q*d = {Func_dem(P_solver):.4f}   Q*s = {Func_sup(P_solver):.4f}   P* = {P_solver:.4f}")

Q_star = Func_dem(P_star)
print(f"\nРівноважна точка: Q* = {Q_star:.4f},  P* = {P_star:.4f}")

# Еластичність у точці рівноваги: E = dQ/dP * P*/Q*
Ed = (235.56*(-0.378)*np.exp(-0.378*P_star)) * (P_star/Q_star)
Es = (65.031/P_star) * (P_star/Q_star)
print(f"Ed = {Ed:.4f}   Es = {Es:.4f}")

# Стабільність
if abs(Ed) > Es:
    state = "стабільна динамічна рівновага"
elif abs(Ed) < Es:
    state = "нестабільна динамічна рівновага"
else:
    state = "квазістабільна динамічна рівновага"
print(f"|Ed| = {abs(Ed):.4f}, Es = {Es:.4f}  ->  {state}")

# Графік 2: функції в осях (Q, P) – по горизонталі кількість, по вертикалі ціна
plt.figure(figsize=(8, 5.5))
plt.plot(Func_dem(p), p, color="tab:blue", label="Func_dem")
plt.plot(Func_sup(p), p, color="tab:red", label="Func_sup")
plt.plot(Func_dem(Price), Price, "o", color="tab:blue")
plt.plot(Func_sup(Price), Price, "s", color="tab:red")
plt.plot(Q_star, P_star, "o", color="gold", mec="k", ms=10,
         label=f"(Q*, P*) = ({Q_star:.2f}; {P_star:.2f})")
plt.xlabel("Q"); plt.ylabel("P")
plt.title("Ринкова рівновага")
plt.legend(); plt.grid(alpha=.3)
plt.savefig("punkt2_equilibrium.png", dpi=130, bbox_inches="tight")


# === ПУНКТ 3 ===
print("\n" + "=" * 25, "ПУНКТ 3", "=" * 25)

# Субсидія для виробника: виробник отримує P + sub,
# тому нова функція пропозиції Qs(sub) = F(P + sub) – крива зсувається вправо
def Sup_sub(P): return 65.031*np.log(P + sub) - 14.104

# Рівновага після субсидії: Q_d(P) - Qs(sub)(P) = 0
P_2 = brentq(lambda P: Func_dem(P) - Sup_sub(P), 0.5, Price.max())
Q_2 = Func_dem(P_2)
print(f"До субсидії:    Q* = {Q_star:.4f},   P* = {P_star:.4f}")
print(f"Після субсидії: Q**d = {Q_2:.4f},  Q**s(sub) = {Sup_sub(P_2):.4f},  P** = {P_2:.4f}"
      f",  Q**d - Q**s = {Q_2 - Sup_sub(P_2):.2e}")

# Як змінились параметри рівноваги
dP = P_2 - P_star                    # зміни для споживача ( ціни)
comp = sub - abs(dP)                 # компенсація виробника
print(f"\nЗміни для споживача: P** - P* = {dP:.4f}")
print(f"Компенсація виробника: sub - |P** - P*| = {comp:.4f}")
print(f"Ціна, яку отримує виробник: P** + sub = {P_2 + sub:.4f}")
print(f"Зміна кількості товару: Q** - Q* = {Q_2 - Q_star:.4f}")

# Графік 3: графік з п. 2 + нова крива пропозиції та нова точка рівноваги
plt.figure(figsize=(8, 5.5))
plt.plot(Func_dem(p), p, color="tab:blue", label="Func_dem")
plt.plot(Func_sup(p), p, color="tab:red", label="Func_sup")
plt.plot(Sup_sub(p), p, color="tab:purple", ls="--", label="Sup(sub)")
plt.plot(Func_dem(Price), Price, "o", color="tab:blue")
plt.plot(Func_sup(Price), Price, "s", color="tab:red")
plt.plot(Sup_sub(Price), Price, "x", color="tab:purple")
plt.plot(Q_star, P_star, "o", color="gold", mec="k", ms=10,
         label=f"(Q*, P*) = ({Q_star:.2f}; {P_star:.2f})")
plt.plot(Q_2, P_2, "o", color="red", mec="k", ms=10,
         label=f"(Q**, P**) = ({Q_2:.2f}; {P_2:.2f})")
plt.xlabel("Q"); plt.ylabel("P")
plt.title(f"Рівновага після введення субсидії для виробника (sub = {sub})")
plt.legend(); plt.grid(alpha=.3)
plt.savefig("punkt3_subsidy.png", dpi=130, bbox_inches="tight")

plt.show()
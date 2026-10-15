# Модель: dx/dt = r*x*(1 - x/q) - p
# Випадок 3: квота p > rq/4,  p = rq/4 + a^2  (дійсних стаціонарних точок немає)
import numpy as np
import matplotlib.pyplot as plt
from scipy.integrate import solve_ivp

# Вихідні дані: N – номер за списком групи
N = 12
r = 2*N if N <= 8 else (3*N if N <= 16 else 4*N)          # темп росту
q = 200*N if N <= 8 else (300*N if N <= 16 else 400*N)    # ємність середовища
print(f"N = {N}:  r = {r},  q = {q}")

# Випадок 3: p = rq/4 + a^2
a = 60
p = r*q/4 + a**2
print(f"\nВипадок 3. a = {a},  p = rq/4 + a^2 = {p:g}")

b, c = np.roots([-r/q, r, -p])               
print(f"Корені: {b:.0f}, {c:.0f}  -> комплексні, дійсних стаціонарних точок немає")

def d1(t, x):                                 # права частина рівняння
    return r*x*(1 - x/q) - p

def extinct(t, x):                            # подія: популяція вимерла (x = 0)
    return x[0]
extinct.terminal = True

T = 0.45                                       # проміжок часу для графіка
x0_list = [q//3, 3*q//4]                       # x0 = q/3,  x0 = 3q/4
colors = ["blue", "green"]

plt.figure(figsize=(8, 5))
for x0, col in zip(x0_list, colors):
    sol = solve_ivp(d1, [0, T], [x0], events=extinct, max_step=0.0005)  # аналог dsolve
    plt.plot(sol.t, sol.y[0], color=col, label=f"x0 = {x0}")
    te = sol.t_events[0][0]
    plt.plot(te, 0, "o", color=col)
    print(f"x0 = {x0}: популяція вимирає за час t* ≈ {te:.4f}")

plt.axhline(q, color="black", ls=":", lw=2, label=f"q = {q}")
plt.xlim(0, T); plt.ylim(0, q*1.05)
plt.xlabel("t"); plt.ylabel("x(t)")
plt.title(f"Випадок 3: p = rq/4 + a² = {p:g}  (a = {a})")
plt.legend(); plt.grid(alpha=.3)
plt.savefig("case3.png", dpi=130, bbox_inches="tight")
plt.show()

# Висновок: незалежно від початкової чисельності популяція прямує до нуля (вимирає за скінченний час).
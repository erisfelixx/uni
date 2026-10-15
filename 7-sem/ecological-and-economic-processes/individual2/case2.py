# Модель: dx/dt = r*x*(1 - x/q) - p
# Випадок 2: квота p < rq/4,  p = rq/4 - eps^2  (дві стаціонарні точки)
import numpy as np
import matplotlib.pyplot as plt
from scipy.integrate import solve_ivp

# Вихідні дані: N – номер за списком групи
N = 12
r = 2*N if N <= 8 else (3*N if N <= 16 else 4*N)          # темп росту
q = 200*N if N <= 8 else (300*N if N <= 16 else 400*N)    # ємність середовища
print(f"N = {N}:  r = {r},  q = {q}")

# Випадок 2: p = rq/4 - eps^2 
# Після віднімання від p параметра eps^2 (eps > 0) квота стає меншою за критичну
eps = 60
p = r*q/4 - eps**2
print(f"\nВипадок 2. eps = {eps},  p = rq/4 - eps^2 = {p:g}")

b, c = sorted(np.roots([-r/q, r, -p]).real)
print(f"Стаціонарні точки: x1 = {b:g},  x2 = {c:g}")

def d1(t, x):                                 # права частина рівняння
    return r*x*(1 - x/q) - p

def extinct(t, x):                            # подія: популяція вимерла (x = 0)
    return x[0]
extinct.terminal = True

T = 0.6                                        # проміжок часу для графіка
x0_list = [1000, 1800, 3000]                   # x0 < x1,  x1 < x0 < x2,  x2 < x0 < q
colors = ["blue", "green", "magenta"]

plt.figure(figsize=(8, 5))
for x0, col in zip(x0_list, colors):
    sol = solve_ivp(d1, [0, T], [x0], events=extinct, max_step=0.0005)
    plt.plot(sol.t, sol.y[0], color=col, label=f"x0 = {x0}")
    if sol.t_events[0].size:
        te = sol.t_events[0][0]
        plt.plot(te, 0, "o", color=col)
        print(f"x0 = {x0}: популяція вимирає за час t* ≈ {te:.4f}")
    else:
        print(f"x0 = {x0}: x({T}) ≈ {sol.y[0][-1]:.2f}  ->  прямує до {c:g}")

plt.axhline(b, color="red", ls=":", lw=2, label=f"x1 = {b:g} (нестійка)")
plt.axhline(c, color="orange", ls=":", lw=2, label=f"x2 = {c:g} (стійка)")
plt.axhline(q, color="black", ls=":", lw=2, label=f"q = {q}")
plt.xlim(0, T); plt.ylim(0, q*1.05)
plt.xlabel("t"); plt.ylabel("x(t)")
plt.title(f"Випадок 2: p = rq/4 − ε² = {p:g}  (ε = {eps})")
plt.legend(); plt.grid(alpha=.3)
plt.savefig("case2.png", dpi=130, bbox_inches="tight")
plt.show()

# Висновок: стаціонарна точка x2 – стійка, бо до неї прямують траєкторії при t -> +inf;
# x1 – нестійка, бо траєкторії від неї розбігаються;
# при x0 < x1 популяція прямує до нуля.
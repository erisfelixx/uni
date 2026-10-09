#task1 - isol_pop (var4)


import numpy as np
import matplotlib.pyplot as plt
 
eps, K = 0.8, 100          # e = 0.008*100, K - ємність середовища
t_check = 3
 
def P(t, P0):
    """Розв'язок логістичного рівняння (модель Верхюльста)"""
    return K * P0 / (P0 + (K - P0) * np.exp(-eps * t))
 
for P0 in (50, 180):
    print(f"P0 = {P0}:  P({t_check}) = {P(t_check, P0):.2f},  при t -> +inf  P -> {K}")
 
t = np.linspace(0, 8, 400)
plt.figure(figsize=(7, 4.5))
for P0 in (50, 180):
    plt.plot(t, P(t, P0), label=f"P0 = {P0}")
plt.axhline(K, ls="--", c="gray", label="K = 100")
plt.axvline(t_check, ls=":", c="k", label="t = 3")
plt.xlabel("t, міс."); plt.ylabel("P(t)")
plt.title("dP/dt = 0.008 P (100 − P)")
plt.legend(); plt.grid(alpha=.3)
plt.savefig("v4_1_izol.png", dpi=130, bbox_inches="tight")
plt.show()
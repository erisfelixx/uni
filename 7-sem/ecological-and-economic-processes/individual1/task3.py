#task3 - prey-pred (var4)


import numpy as np
import matplotlib.pyplot as plt
from scipy.integrate import solve_ivp

e1, e2, g1, g2 = 5, 3, 3, 5      # ε1, ε2, γ1, γ2
ICS = [(1.5, 0.5), (0.5, 3)]     # а) x0 > y0,  б) x0 < y0

def model(beta):
    return lambda t, z: [z[0] * (e1 - g1 * z[1] - beta * z[0]),
                         z[1] * (-e2 + g2 * z[0])]

def jacobian(beta, x, y):
    return np.array([[e1 - g1 * y - 2 * beta * x, -g1 * x],
                     [g2 * y, -e2 + g2 * x]])

def study(beta, name, title, points):
    f = model(beta)
    print(f"\n===== {title} =====")
    for p in points:
        lam = np.linalg.eigvals(jacobian(beta, *p))
        print(f"Точка ({p[0]:.3f}; {p[1]:.3f}):  λ = {np.round(lam, 3)}")

    # 1. Фазовий портрет
    fig, ax = plt.subplots(figsize=(7, 6))
    X, Y = np.meshgrid(np.linspace(-0.5, 4, 25), np.linspace(-0.5, 6, 25))
    U, V = f(0, [X, Y]); M = np.hypot(U, V); M[M == 0] = 1
    ax.quiver(X, Y, U / M, V / M, color="gray", alpha=.5, width=.003)
    for z0 in [(0.7, 1.8), (1, 1.5), (1.5, 0.5), (0.5, 3), (2, 1), (0.3, 0.5)]:
        s = solve_ivp(f, [0, 15], z0, max_step=.005)
        ax.plot(s.y[0], s.y[1], lw=1.3)
    # траєкторії в інших чвертях (повний фазовий портрет)
    stop = lambda t, z: abs(z[0]) + abs(z[1]) - 20   # зупинка, коли розв'язок "тікає"
    stop.terminal = True
    for z0 in [(-0.2, 0.5), (-0.3, 2), (0.5, -0.2), (2, -0.2), (-0.2, -0.2)]:
        s = solve_ivp(f, [0, 3], z0, max_step=.005, events=stop)
        ax.plot(s.y[0], s.y[1], lw=1.3, ls="--")
    for p in points:
        ax.plot(*p, "ko", ms=7)
    ax.axhline(0, c="k", lw=.8); ax.axvline(0, c="k", lw=.8)
    ax.set_xlim(-0.5, 4); ax.set_ylim(-0.5, 6)
    ax.set_xlabel("x (жертви)"); ax.set_ylabel("y (хижаки)")
    ax.set_title("Фазовий портрет: " + title)
    fig.savefig(name + "_phase.png", dpi=130, bbox_inches="tight")

    # 2. Динаміка популяцій
    fig, axs = plt.subplots(1, 2, figsize=(12, 4.2))
    for ax, z0, lab in zip(axs, ICS, ["а) x0 > y0", "б) x0 < y0"]):
        s = solve_ivp(f, [0, 8], z0, max_step=.005)
        ax.plot(s.t, s.y[0], label="x(t) жертви")
        ax.plot(s.t, s.y[1], label="y(t) хижаки")
        ax.set_title(f"{title}, {lab}: x0={z0[0]}, y0={z0[1]}")
        ax.set_xlabel("t"); ax.legend(); ax.grid(alpha=.3)
    fig.savefig(name + "_dynamics.png", dpi=130, bbox_inches="tight")

    # 3. 3D-графік
    fig = plt.figure(figsize=(8, 6)); ax = fig.add_subplot(projection="3d")
    for z0 in ICS:
        s = solve_ivp(f, [0, 8], z0, max_step=.005)
        ax.plot(s.t, s.y[0], s.y[1], label=f"x0={z0[0]}, y0={z0[1]}")
    ax.set_xlabel("t"); ax.set_ylabel("x"); ax.set_zlabel("y")
    ax.set_title("3D графік: " + title); ax.legend()
    fig.savefig(name + "_3d.png", dpi=130, bbox_inches="tight")

# А) Вольтерра (β = 0)
study(0, "v4_2_volterra", "модель Вольтерра",
      [(0, 0), (e2 / g2, e1 / g1)])
# Б) Лоткі–Вольтерра (β = 1.5)
beta = 1.5
study(beta, "v4_3_lotka_volterra", "модель Лоткі–Вольтерра (β=1.5)",
      [(0, 0), (e1 / beta, 0), (e2 / g2, (e1 * g2 - beta * e2) / (g1 * g2))])
plt.show()
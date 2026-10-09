#task2 - lesli (var4)


import numpy as np
 
b = [0, 0, 0.19, 0.44, 0.5, 0.5, 0.45]   #коефіцієнти народжуваності
 
def leslie(s, s_last):
    """Матриця Леслі 7x7: s – коефіцієнти переходу, s_last – виживання у групі 12+"""
    L = np.zeros((7, 7))
    L[0] = b
    for i in range(6):
        L[i + 1, i] = s
    L[6, 6] = s_last
    return L
 
def analyze(L, title):
    print(f"\n- {title} -")
    print("Матриця Леслі:\n", np.round(L, 3))
    print("Коефіцієнти характеристичного многочлена:", np.round(np.poly(L), 4))
    w, v = np.linalg.eig(L)
    k = np.argmax(w.real)
    lam = w[k].real                          
    x = np.abs(v[:, k].real); x = x / x[-1]  
    H = (1 - 1 / lam) * 100
    print(f"Швидкість росту  λ_L = {lam:.4f}")
    print("Стійка вікова структура x_L =", np.round(x, 3))
    print("У відсотках:", np.round(x / x.sum() * 100, 1))
    print(f"Частка вилову  H = {H:.2f} %")
 
analyze(leslie(0.87, 0.8), "Початкова задача")
analyze(leslie(0.825, 0.775), "Після змін (0.825; 0.775)")

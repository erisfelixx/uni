#task1 - isol_pop (var4)

import sympy as sp

t = sp.symbols('t')
P = sp.Function('P')
ode = sp.Eq(P(t).diff(t), sp.Rational(8, 1000) * P(t) * (100 - P(t)))

for P0 in (50, 180):
    sol = sp.dsolve(ode, P(t), ics={P(0): P0})
    print(f"P0 = {P0}:", sol)
    print("   P(3) =", sp.N(sol.rhs.subs(t, 3), 5))
    print("   t -> oo:", sp.limit(sol.rhs, t, sp.oo))
#!/usr/bin/env python3
"""Apply the A/B decision rule in ab-test-plan.md.

usage: python3 ab_decide.py A_INVITES A_YESMAYBE A_NO A_REGISTERED B_INVITES B_YESMAYBE B_NO B_REGISTERED
"""
import math, sys


def z_p(x1, n1, x2, n2):
    p = (x1 + x2) / (n1 + n2)
    se = math.sqrt(p * (1 - p) * (1 / n1 + 1 / n2))
    if se == 0:
        return 0.0, 1.0
    z = (x1 / n1 - x2 / n2) / se
    return z, math.erfc(abs(z) / math.sqrt(2))


def main(a):
    ai, ay, an, ar, bi, by, bn, br = map(int, a)
    if min(ai, bi) < 40000:
        print(f"WAIT: each variant needs 40,000 invites sent (A {ai:,}, B {bi:,}). No decision yet.")
        return
    for label, xa, xb in (("Registration rate", ar, br), ("Yes/Maybe rate", ay, by), ("No rate", an, bn)):
        z, p = z_p(xa, ai, xb, bi)
        print(f"{label}: A {xa / ai:.3%}  B {xb / bi:.3%}  p={p:.4f}")
    for label, xa, xb in (("registration rate", ar, br), ("Yes/Maybe rate", ay, by)):
        z, p = z_p(xa, ai, xb, bi)
        if p < 0.05:
            win, lose = ("A", "B") if z > 0 else ("B", "A")
            nw, nl = (an / ai, bn / bi) if win == "A" else (bn / bi, an / ai)
            if nw - nl > 0.01:
                print(f"NO WINNER: {win} leads on {label} but its No rate is over 1 point higher. Keep A, rerun.")
                return
            print(f"WINNER: {win} on {label} (p={p:.4f}). {win} becomes next week's control.")
            return
    print("NO WINNER: no difference at p < 0.05. Keep A as control; next week test a new challenger against it.")


if __name__ == "__main__":
    if len(sys.argv) != 9:
        sys.exit(__doc__)
    main(sys.argv[1:])

import sys; sys.path.insert(0, '/tmp/claude-0/-home-claude/65cbdb2d-2e97-5541-aafa-56986837a43b/scratchpad/w03probe')
from harness import run
import numpy as np
base = """O1 inv_p 0 arr_p 0 LTA
.model LTA LTRA R=6.780m L=593.0n G=0 C=37.526p LEN=936 {mx}
Isw 0 arr_p PWL(0 18.4 1u 18.4 2u 0)
{clamp}
{carr}
Vmi inv_p cin_p 0
Cin cin_p 0 150u
RL cin_p 0 62.1685
"""
clamps = {
 "dz": """Dp arr_p kp DCL
Vkp kp 0 1500
Dn kn arr_p DCL
Vkn 0 kn 1500
.model DCL D(IS=1e-12 N=1 RS=0.05)""",
 "bv": """Dp arr_p kq DBV
Dn 0 kq DBV
.model DBV D(IS=1e-12 N=1 RS=0.05 BV=1500 IBV=1m)""",
}
for cn, cl in clamps.items():
    for carr in ["", "Carr arr_p 0 1n"]:
        for mx in ["", "NOCONTROL"]:
            name = f"t1_{cn}_{'c' if carr else 'n'}_{mx or 'def'}"
            dt, msg, d = run(name, base.format(mx=mx, clamp=cl, carr=carr), vecs="v(arr_p) i(vmi)")
            if d is None: print(name, f"{dt:.1f}s", msg[:2]); continue
            t, va, ii = d.T
            print(name, f"{dt:.1f}s rows={len(t)} tend={t[-1]*1e6:.2f}us Vmax={va.max():.1f} Vmin={va.min():.1f} Iinv_min={ii.min():.3f}", msg[:1])

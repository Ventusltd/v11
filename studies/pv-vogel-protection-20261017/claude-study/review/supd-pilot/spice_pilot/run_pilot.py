"""SUP-D pilot of the wave-2 reproducibility protocol on a closed-form RLC case (ILLUSTRATIVE, not a fault model).
Runs ngspice -b twice (tstep h and h/2), parses wrdata, computes E = int v*i dt with scipy trapezoid, compares to the
analytic energy 0.5*C*V0^2, reports relative changes and sha256 of decimated exports. Deterministic."""
import hashlib, subprocess, sys, numpy as np
from pathlib import Path
from scipy.integrate import trapezoid
HERE = Path(__file__).resolve().parent
C, V0, L, R = 150e-6, 1143.9, 0.6674e-3, 2.0
E_analytic = 0.5 * C * V0 ** 2
NET = """* SUP-D pilot RLC discharge; ILLUSTRATIVE
C1 n1 0 {C} ic={V0}
L1 n1 n2 {L}
Vs n2 n3 0
R1 n3 0 {R}
.tran {h} 20m 0 {h} uic
.options reltol=1e-4 abstol=1e-9 vntol=1e-6 method=gear
.control
run
wrdata {out} v(n3) i(Vs)
quit
.endc
.end
"""
def run(h, tag):
    cir = HERE / f"rlc_{tag}.cir"; out = HERE / f"rlc_{tag}.dat"
    cir.write_text(NET.format(C=C, V0=V0, L=L, R=R, h=h, out=out))
    r = subprocess.run(["ngspice", "-b", str(cir)], capture_output=True, text=True, timeout=300)
    if r.returncode != 0:
        print(r.stdout[-2000:], r.stderr[-2000:]); sys.exit(1)
    d = np.loadtxt(out)              # columns: t v  t i
    t, v, i = d[:, 0], d[:, 1], d[:, 3]   # i(Vs): positive when flowing from + node (n2) through the source to - node (n3), i.e. INTO the load
    return t, v, i
res = {}
for tag, h in (("h", 1e-6), ("h2", 0.5e-6)):
    t, v, i = run(h, tag)
    E = trapezoid(v * i, t)
    dec = np.c_[t, v, i][::10]
    csv = HERE / f"rlc_{tag}_dec10.csv"; np.savetxt(csv, dec, delimiter=",", header="t_s,v_fault_v,i_fault_a", comments="")
    res[tag] = (E, len(t), hashlib.sha256(csv.read_bytes()).hexdigest())
    print(f"tstep={h:.1e} s  points={len(t)}  E_scipy_trapezoid={E:.4f} J  rel_vs_analytic={(E-E_analytic)/E_analytic:+.2e}  sha256(dec10)={res[tag][2][:16]}")
print(f"E_analytic=0.5*C*V0^2={E_analytic:.4f} J ; time-step halving relative change in E = {(res['h2'][0]-res['h'][0])/res['h'][0]:+.2e}")
print("zeta =", R / 2 * (C / L) ** 0.5, "(overdamped if > 1); tau_RC-ish =", R * C, "s; L/R =", L / R, "s")

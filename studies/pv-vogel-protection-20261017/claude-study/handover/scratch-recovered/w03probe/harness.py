import subprocess, sys, time, numpy as np, pathlib
D = pathlib.Path(__file__).parent
def run(name, body, tstop="100u", tstep="2n", tmax="5n", vecs="v(arr_p) i(vmi)", opts="reltol=1e-4", timeout=25):
    cir = D / f"{name}.cir"; out = D / f"{name}.txt"
    if out.exists(): out.unlink()
    cir.write_text(f"* {name}\n{body}\n.options {opts}\n.control\ntran {tstep} {tstop} 0 {tmax}\nset wr_singlescale\nset wr_vecnames\noption numdgt=10\nwrdata {out.name} {vecs}\nquit\n.endc\n.end\n")
    t0 = time.time()
    try:
        p = subprocess.run(["ngspice", "-b", cir.name], cwd=D, capture_output=True, text=True, timeout=timeout)
        msg = [l for l in (p.stdout + p.stderr).splitlines() if "trouble" in l or "abort" in l or "rror" in l]
    except subprocess.TimeoutExpired:
        msg = ["TIMEOUT"]
    dt = time.time() - t0
    if out.exists():
        d = np.loadtxt(out, skiprows=1)
        return dt, msg, d
    return dt, msg, None

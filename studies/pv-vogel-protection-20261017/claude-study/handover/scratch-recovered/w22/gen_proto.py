import math, sys
k=1.380649e-23; q=1.602176634e-19; T=298.15; Vt=k*T/q
N=1.3*22; Rs=0.02; Rsh=500.0; Voc=45.75/3; Isc=18.4
IS=(Isc - Voc/Rsh)/math.expm1(Voc/(N*Vt))
Nb=1.1; RSb=0.005; ISb=17/math.expm1((0.45-RSb*17)/(Nb*Vt))
G=float(sys.argv[1]); a=float(sys.argv[2]); gap=float(sys.argv[3]); mode=sys.argv[4]; I0=float(sys.argv[5]) if len(sys.argv)>5 else 0
tstep=float(sys.argv[6]) if len(sys.argv)>6 else 1e-6
iph=18.4*G/1000
R=2*936*3.39e-3; L=936*(0.613+0.1)*1e-6
K=a+0.534*gap
lines=["* proto C1in", ".options temp=25 tnom=25 reltol=1e-4 abstol=1e-9 vntol=1e-6 method=gear",
f".model DCELL D(IS={IS:.10e} N={N:.6f})", f".model DBYP D(IS={ISb:.10e} N={Nb} RS={RSb})",
".subckt SS lo hi params: iph=18.4", "Iph lo c DC {iph}", "Dc c lo DCELL", f"Rsh c lo {Rsh}", f"Rs c hi {Rs}", ".ends SS",
".subckt MOD jm jp params: iph=18.4", "XA jm na SS iph={iph}", "XB na nb SS iph={iph}", "XC nb jp SS iph={iph}",
"DA jm na DBYP", "DB na nb DBYP", "DC nb jp DBYP", ".ends MOD"]
for mm in range(1,31):
    if mm==15: continue
    lines.append(f"XM{mm} n{mm-1} n{mm} MOD iph={iph}")
# M15 flattened
lines += [f"XS1 n14 n15a SS iph={iph}", "Vsd1 n14 d1a 0", "D1 d1a n15a DBYP",
 f"Iph2 n15a c2 DC {iph}", "Dc2 c2 n15a DCELL", f"Rsh2 c2 n15a {Rsh}", f"Rs2 c2 m {Rs}",
 "Barc m x V = v(sig)*%.6f*i(Vsarc)*pow(i(Vsarc)*i(Vsarc)+1e-4,-0.44)" % K,
 "Vsarc x n15b 0", "Vsd2 n15a d2a 0", "D2 d2a n15b DBYP",
 f"XS3 n15b n15 SS iph={iph}", "Vsd3 n15b d3a 0", "D3 d3a n15 DBYP",
 "Vsig sig 0 PWL(0 0 0.5m 0 0.501m 1)" if mode!="noarc" else "Vsig sig 0 0",
 f"Rp n30 lp {R/2}", f"Lp lp invl {L/2}", "Vsstr invl invp 0",
 f"Rn 0 ln {R/2}", f"Ln ln n0 {L/2}"]
if mode=="op":
    lines += ["Vnode invp 0 DC 1143.9", ".control", "op", "print i(Vnode) v(n30) v(n0)", "quit", ".endc", ".end"]
else:
    lines += ["Cin invp 0 150u", f"Isink invp 0 DC {I0:.12g}",
      "Bmeter 0 em I = (v(m)-v(x))*i(Vsarc)", "Cmeter em 0 1m", "Rmeter em 0 1e12",
      f".tran {tstep} 20m 0 {tstep}", ".control", "set wr_singlescale", "set wr_vecnames", "option numdgt=12", "run",
      "wrdata out.dat i(Vsarc) v(m,x) i(Vsd2) i(Vsstr) v(invp) v(n30,n0) v(n15,n14) v(em)", "quit", ".endc", ".end"]
print("\n".join(lines))

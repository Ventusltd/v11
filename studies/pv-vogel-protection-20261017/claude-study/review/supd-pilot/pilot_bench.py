"""SUP-D pilot (NOT the W06 benchmark): small equal-budget calculations to set criteria.
2-D and 4-D, N in {64,256,1024}, seed 20261017. Metrics: CD discrepancy, min pairwise distance,
corner-box coverage (delta=0.1), planted-region misses. Deterministic."""
import math, numpy as np
from scipy.stats import qmc
from scipy.spatial.distance import pdist

GOLDEN = math.pi * (3 - math.sqrt(5))
SEED = 20261017

def vogel2d(N):
    n = np.arange(1, N + 1)
    r = np.sqrt((n - 0.5) / N); t = n * GOLDEN
    return np.c_[0.5 + 0.5 * r * np.cos(t), 0.5 + 0.5 * r * np.sin(t)]

def vogel_scrambled(N, d, rng):
    """d even: independent random permutation of the Vogel index per 2-D pair (documented pairing)."""
    cols = []
    for p in range(d // 2):
        P = vogel2d(N)[rng.permutation(N)]
        cols += [P[:, 0], P[:, 1]]
    return np.c_[tuple(cols)]

def grid_corners(N, d):
    """full factorial grid with m^d <= N - 2^d points plus the 2^d corners (explicit)."""
    corners = np.array(np.meshgrid(*[[0.0, 1.0]] * d)).reshape(d, -1).T
    m = max(2, int(math.floor((N - len(corners)) ** (1 / d))))
    axes = [(np.arange(m) + 0.5) / m] * d
    g = np.array(np.meshgrid(*axes)).reshape(d, -1).T
    X = np.vstack([corners, g])
    return X[:N]

def designs(N, d, seed):
    rng = np.random.default_rng(seed)
    out = {}
    if d == 2:
        out["vogel_bounded"] = vogel2d(N)
    else:
        out["vogel_scrambled_pairs"] = vogel_scrambled(N, d, rng)
    out["sobol_scrambled"] = qmc.Sobol(d, scramble=True, seed=seed).random(N)
    out["lhs"] = qmc.LatinHypercube(d, seed=seed).random(N)
    out["pseudo_random"] = np.random.default_rng(seed).random((N, d))
    out["grid_plus_corners"] = grid_corners(N, d)
    return out

def corner_coverage(X, delta=0.1):
    d = X.shape[1]; hit = 0
    for c in range(2 ** d):
        ok = np.ones(len(X), bool)
        for a in range(d):
            hi = (c >> a) & 1
            ok &= (X[:, a] >= 1 - delta) if hi else (X[:, a] <= delta)
        hit += ok.any()
    return hit / 2 ** d

def regions(d):
    R = {}
    R["R1_corner_box_0.9"] = lambda X: np.all(X[:, :2] >= 0.9, axis=1)                  # area 0.01 on first pair
    R["R2_thin_slab_u1<0.02"] = lambda X: X[:, 0] <= 0.02                                 # volume 0.02
    R["R3_ball_c(0.37,0.61)_r0.06"] = lambda X: np.hypot(X[:, 0] - 0.37, X[:, 1] - 0.61) <= 0.06  # area 0.0113
    R["R4_diag_ridge_|u1-u2|<0.02"] = lambda X: np.abs(X[:, 0] - X[:, 1]) <= 0.02          # area 0.0396
    R["R5_categorical_holdout"] = lambda X: (X[:, 0] >= 0.5) & (X[:, 1] < 0.5) & (X[:, 1 if d == 2 else 2] >= 0.8) & (X[:, 1 if d == 2 else 3] <= 0.1)
    if d >= 4:
        R["R6_cross_pair_corner_u1>0.95&u3>0.95"] = lambda X: (X[:, 0] >= 0.95) & (X[:, 2] >= 0.95)  # area 0.0025
    return R

for d in (2, 4):
    print(f"\n=== d={d} seed={SEED} ===")
    print(f"{'N':>5} {'design':<24} {'CD_disc':>9} {'min_dist':>9} {'corner_cov':>10}  misses")
    for N in (64, 256, 1024):
        D = designs(N, d, SEED); R = regions(d)
        for name, X in D.items():
            disc = qmc.discrepancy(X, method="CD")
            md = pdist(X).min()
            cc = corner_coverage(X)
            miss = [k for k, f in R.items() if not f(X).any()]
            print(f"{N:>5} {name:<24} {disc:9.5f} {md:9.5f} {cc:10.3f}  {len(miss)}/{len(R)} {[m.split('_')[0] for m in miss]}")
# analytic: bounded Vogel disk never reaches the corner box
print("\nAnalytic: nearest point of [0.9,1]^2 to disk centre is (0.9,0.9), distance", round(math.hypot(0.4, 0.4), 4), "> 0.5 radius -> R1 unreachable at ANY N")
print("Disk area fraction of unit square:", round(math.pi / 4, 4), "; corner area never sampled:", round(1 - math.pi / 4, 4))
print("Expected uniform hits in a 6-D corner box delta=0.1 at N=1024:", 1024 * 0.1 ** 6)

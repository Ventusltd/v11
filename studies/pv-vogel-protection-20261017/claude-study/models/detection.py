"""Detection / sensing-chain library — V11 cycle-1 PV protection study, Track C (worker W05).

STATUS: ILLUSTRATIVE.  Deterministic, sample-based models of sensing channels plus a rule-based
classifier.  Nothing here is a validated arc detector.  Every number this module produces is graded
`algebra` or `illustrative_simulation` (a simulation of the DETECTION CHAIN on synthetic or
algebraically derived waveforms, not of fault physics).

* The HF channel has NO physical arc model behind it (the ngspice arc model has no HF physics).
  It refuses any waveform that does not carry the SYNTHETIC label; its true-positive performance on
  real arcs is UNKNOWN.
* Thresholds were chosen with knowledge of the synthetic benign set (benign_set.py); zero false trips
  on that set is a consistency check, NOT a validation and NOT a nuisance-trip rate.
* Probabilities / rates are never inferred.

Run from claude-study/:   python3 models/detection.py   -> models/detection-latency-budget.json
"""
from __future__ import annotations

import hashlib
import json
import math
import zlib
from dataclasses import dataclass, asdict
from pathlib import Path

import numpy as np
import scipy
from scipy import optimize
from scipy import signal as sps

HERE = Path(__file__).resolve().parent
STUDY = HERE.parent
FIXTURE_PATH = STUDY / "fixture" / "system-fixture.json"
LATENCY_JSON = HERE / "detection-latency-budget.json"
SYNTHETIC = "SYNTHETIC"
MODEL_REVISION = "W05-detection-v1"


# ----------------------------------------------------------------------------------------------
# Fixture (the ONLY source of plant numbers)
# ----------------------------------------------------------------------------------------------
def _load_fixture(path: Path = FIXTURE_PATH):
    raw = path.read_bytes()
    return json.loads(raw), hashlib.sha256(raw).hexdigest()


FX, FX_SHA256 = _load_fixture()
_MOD, _PLANT, _CON = FX["module"], FX["plant"], FX["conductors"]
IMPP_A = _MOD["impp_a"]                                   # 17.31
ISC_A = _MOD["isc_a"]                                     # 18.4
VMPP_MOD_V = _MOD["vmpp_v"]                               # 38.13
VOC_MOD_V = _MOD["voc_stc_v"]                             # 45.75
PMPP_COEFF = _MOD["pmpp_temp_coeff_per_c"]["value"]       # -0.0034 ASSUMED (fixture)
ISC_COEFF = _MOD["isc_temp_coeff_per_c"]["value"]         # +0.0005 ASSUMED (fixture)
SUBSTRINGS = _MOD["internal_structure"]["substrings_per_module"]
LEAD_M = _MOD["internal_structure"]["positive_lead_m"] + _MOD["internal_structure"]["negative_lead_m"]
BYPASS_VF_V = 0.45                                        # fixture text: "Schottky_assumed_Vf_0p45_V_at_17A"
assert "0p45" in _MOD["internal_structure"]["bypass_diode_type"]
N_MOD = _PLANT["modules_per_string"]                      # 30
VMPP_STR_V = _PLANT["string_derived"]["vmpp_string_v"]    # 1143.9
FIELD = _CON["field_cable"]
LEAD = _CON["factory_lead"]
R_FIELD_OHM_PER_M = FIELD["resistance_ohm_per_km_20c"] / 1000.0
R_LEAD_OHM_PER_M = LEAD["resistance_ohm_per_km_20c"] / 1000.0
ALPHA_CU = FIELD["temp_coeff_per_c"]                      # 0.00393 /C
R_CONN_OHM = _CON["connector_resistance_ohm_each"]        # 0.00035
N_MATES = _CON["mated_interfaces_per_string"]["total"]    # 33
V_PROP_M_PER_S = _CON["two_wire_line_defaults"]["propagation_velocity_m_per_s"]
DELAY_936_US = _CON["two_wire_line_defaults"]["one_way_delay_936m_us"]   # 4.415
_C1, _C2, _C3 = (FX["priority_cases"][k] for k in ("C1", "C2", "C3"))
ROUTE_S20_M = _C2["string_route_m"]["S20"]               # 936
ROUTE_S19_M = _C2["string_route_m"]["S19"]               # 600
C_IN_F = FX["inverter_dc_side"]["mppt_input_capacitance_f"]["value"]
AFCI_DETECT_TO_TRIP_S = FX["existing_conventional_protection_baseline_P0"]["inverter_afci"]["detect_to_trip_s_variants"]
_ARC = FX["arc_model"]
assert "(20 + 0.534 * gap_mm) * I^0.12" in _ARC["static_vi_law"], "fixture arc law changed"
ARC_A0_V, ARC_A1_V_PER_MM, ARC_EXP = 20.0, 0.534, 0.12
ARC_I_MIN_A = _ARC["minimum_sustaining_current_a"]["value"]
C3_TH = _C3["thermal"]
C3_C_TH_J_PER_K = C3_TH["connector_thermal_mass_j_per_k"]["value"]   # 8 ASSUMED
C3_H_W_PER_K = C3_TH["connector_to_ambient_w_per_k"]["value"]        # 0.25 ASSUMED
C3_T_AMB_C = C3_TH["ambient_c"]                                     # 35
C3_R_VARIANTS_OHM = _C3["resistance_variants_ohm"]                  # [0.05, 0.2, 1.0]
C3_RAMP_S = 600.0
assert "over 600 s" in _C3["fault_phase"] and "0.00035" in _C3["fault_phase"]


def lab(value, label, grade, note=None, **extra):
    """Labelled number for JSON export (units are carried by the key suffix)."""
    d = {"value": value, "label": label, "grade": grade}
    if note:
        d["note"] = note
    d.update(extra)
    return d


def seed_of(*parts) -> int:
    """Deterministic seed from a tuple of identifiers (no wall clock, no global RNG)."""
    return zlib.crc32("|".join(str(p) for p in parts).encode())


def rnd(x, sig=6):
    """Round floats for stable JSON (None/inf preserved as strings)."""
    if x is None:
        return None
    if isinstance(x, (bool, np.bool_)):
        return bool(x)
    if isinstance(x, (int, np.integer)):
        return int(x)
    x = float(x)
    if math.isinf(x) or math.isnan(x):
        return str(x)
    if x == 0.0:
        return 0.0
    return float(f"{x:.{sig}g}")


# ----------------------------------------------------------------------------------------------
# Labelled waveforms
# ----------------------------------------------------------------------------------------------
@dataclass(frozen=True)
class Signal:
    samples: np.ndarray
    dt_s: float
    labels: frozenset = frozenset()
    t0_s: float = 0.0

    def __post_init__(self):
        object.__setattr__(self, "samples", np.asarray(self.samples, dtype=float))
        object.__setattr__(self, "labels", frozenset(self.labels))

    @property
    def n(self) -> int:
        return int(self.samples.shape[0])

    def times_s(self) -> np.ndarray:
        return self.t0_s + self.dt_s * np.arange(self.n)

    def plus(self, other: "Signal") -> "Signal":
        if other.n != self.n or not math.isclose(other.dt_s, self.dt_s):
            raise ValueError("signals must share length and dt")
        return Signal(self.samples + other.samples, self.dt_s, self.labels | other.labels, self.t0_s)


class SyntheticLabelError(ValueError):
    """Raised when the HF channel is fed a waveform without the SYNTHETIC label."""


# ----------------------------------------------------------------------------------------------
# (a) Sensor chain: front-end clip -> first-order bandwidth -> sample -> gain/offset/noise -> ADC
# ----------------------------------------------------------------------------------------------
@dataclass(frozen=True)
class ChainSpec:
    name: str
    kind: str
    unit: str
    offset: float            # additive offset in measured unit (A or V)
    gain_error: float        # fractional
    noise_rms: float         # white noise at ADC input, measured unit rms
    f_bw_hz: float           # first-order (anti-alias) bandwidth
    adc_bits: int
    full_scale: float        # bipolar +/- full scale
    fs_adc_hz: float
    r_shunt_ohm: float | None = None
    provenance: str = ""

    @property
    def lsb(self) -> float:
        return 2.0 * self.full_scale / 2 ** self.adc_bits

    @property
    def tau_s(self) -> float:
        return 1.0 / (2.0 * math.pi * self.f_bw_hz)


# Kelvin shunt at the module junction box (local reference, no HV isolation needed).
# 25 uV max offset, 0.2 % gain error, 400 kHz amplifier bandwidth: INA240A4 distributor listing
# (https://www.lcsc.com/product-detail/C882770.html, accessed 2026-10-17); TI datasheet PDF NOT EXAMINED.
SHUNT_R_OHM = 0.0005                                      # ASSUMED (brief, PR5 research value)
SHUNT_JB = ChainSpec(
    name="kelvin_shunt_0p5mohm_ina240class_jb", kind="kelvin_shunt", unit="A",
    offset=25e-6 / SHUNT_R_OHM, gain_error=0.002, noise_rms=0.02, f_bw_hz=2000.0,
    adc_bits=12, full_scale=50.0, fs_adc_hz=20000.0, r_shunt_ohm=SHUNT_R_OHM,
    provenance="offset/gain from INA240A4 listing; noise, 2 kHz anti-alias RC, 12-bit +/-50 A, 20 kS/s ASSUMED")
# Generic closed-loop fluxgate at the string ends (galvanic isolation at up to 1500 V common mode).
FLUXGATE_STR = ChainSpec(
    name="generic_closed_loop_fluxgate_string_end", kind="fluxgate", unit="A",
    offset=0.05, gain_error=0.003, noise_rms=0.02, f_bw_hz=2000.0,
    adc_bits=12, full_scale=50.0, fs_adc_hz=20000.0,
    provenance="ALL ASSUMED (generic; CKSR 25-NP listing confirmed only 'fluxgate closed loop 25 A', specs not retrieved)")
VSENSE_MODULE = ChainSpec(
    name="module_terminal_voltage", kind="divider_adc", unit="V", offset=0.05, gain_error=0.005,
    noise_rms=0.02, f_bw_hz=2000.0, adc_bits=12, full_scale=64.0, fs_adc_hz=20000.0,
    provenance="0.5 % gain error per task; others ASSUMED")
VSENSE_STRING = ChainSpec(
    name="string_voltage", kind="isolated_divider_adc", unit="V", offset=0.5, gain_error=0.005,
    noise_rms=0.3, f_bw_hz=2000.0, adc_bits=12, full_scale=1600.0, fs_adc_hz=20000.0,
    provenance="0.5 % gain error per task (5.72 V at 1143.9 V); others ASSUMED")

LOCATIONS = ("module_jb", "string_array_end", "string_inverter_end")
CURRENT_CHAIN = {"module_jb": SHUNT_JB, "string_array_end": FLUXGATE_STR, "string_inverter_end": FLUXGATE_STR}
VOLTAGE_CHAIN = {"module_jb": VSENSE_MODULE, "string_array_end": VSENSE_STRING, "string_inverter_end": VSENSE_STRING}
V_NOMINAL = {"module_jb": VMPP_MOD_V, "string_array_end": VMPP_STR_V, "string_inverter_end": VMPP_STR_V}


def first_order_lowpass(x: np.ndarray, dt_s: float, fc_hz: float) -> np.ndarray:
    """Exact first-order low-pass (pole-matched); state initialised at x[0] (no start-up transient)."""
    alpha = math.exp(-2.0 * math.pi * fc_hz * dt_s)
    b, a = [1.0 - alpha], [1.0, -alpha]
    zi = sps.lfilter_zi(b, a) * x[0]
    y, _ = sps.lfilter(b, a, x, zi=zi)
    return y


def sensor_chain(sig: Signal, spec: ChainSpec, seed: int) -> Signal:
    """Physical waveform (fine dt) -> ADC samples at spec.fs_adc_hz.  Deterministic for a given seed."""
    dec = int(round(1.0 / (spec.fs_adc_hz * sig.dt_s)))
    if dec < 1 or abs(dec * sig.dt_s * spec.fs_adc_hz - 1.0) > 1e-9:
        raise ValueError("simulation dt must divide the ADC period")
    x = np.clip(sig.samples, -spec.full_scale, spec.full_scale)        # front-end saturation
    y = first_order_lowpass(x, sig.dt_s, spec.f_bw_hz)[::dec]
    rng = np.random.default_rng(seed)
    y = (1.0 + spec.gain_error) * y + spec.offset + rng.normal(0.0, spec.noise_rms, y.shape)
    q = np.clip(np.round(y / spec.lsb) * spec.lsb, -spec.full_scale, spec.full_scale - spec.lsb)
    return Signal(q, dec * sig.dt_s, sig.labels | {"CHAIN:" + spec.name}, sig.t0_s)


# ----------------------------------------------------------------------------------------------
# Persistence helpers (vectorised, deterministic)
# ----------------------------------------------------------------------------------------------
def run_length(mask: np.ndarray) -> np.ndarray:
    """r[k] = number of consecutive True samples ending at k (0 where mask is False)."""
    mask = np.asarray(mask, dtype=bool)
    idx = np.arange(mask.size)
    last_false = np.maximum.accumulate(np.where(~mask, idx, -1))
    return np.where(mask, idx - last_false, 0)


def first_index(cond: np.ndarray):
    hits = np.flatnonzero(cond)
    return int(hits[0]) if hits.size else None


def k_of_m(flags: np.ndarray, k: int, m: int) -> np.ndarray:
    """True at frame j when at least k of the frames j-m+1..j are flagged."""
    c = np.convolve(np.asarray(flags, dtype=float), np.ones(m))[: len(flags)]
    return c >= k - 1e-9


def causal_moving_average(x: np.ndarray, w: int) -> np.ndarray:
    c = np.concatenate(([0.0], np.cumsum(x)))
    m = np.full(x.size, np.nan)
    m[w - 1:] = (c[w:] - c[:-w]) / w
    return m


# ----------------------------------------------------------------------------------------------
# (b) Current-step (Delta-I) detector and sign-reversal detector
# ----------------------------------------------------------------------------------------------
@dataclass(frozen=True)
class StepParams:
    window_s: float = 1e-3        # moving-average window W
    lag_s: float = 4e-3           # separation D between compared averages
    theta_abs_a: float = 0.20     # absolute floor
    theta_rel: float = 0.018      # relative to the lagged mean current
    persist_s: float = 3e-3       # N consecutive samples; design rule N > T_burst(1 ms) + W + 3 tau


@dataclass(frozen=True)
class ReversalParams:
    threshold_a: float = -1.0     # I <= -1 A (>> offset 0.05 A + noise 0.02 A rms)
    persist_s: float = 2e-3       # > T_burst(1 ms) + 3 tau


def step_detector(i_adc: Signal, p: StepParams = StepParams()) -> dict:
    fs = 1.0 / i_adc.dt_s
    w, d, n = (int(round(v * fs)) for v in (p.window_s, p.lag_s, p.persist_s))
    m = causal_moving_average(i_adc.samples, w)
    di = np.full(i_adc.n, np.nan)
    di[d:] = m[d:] - m[:-d]
    ref = np.full(i_adc.n, np.nan)
    ref[d:] = np.abs(m[:-d])
    theta = np.maximum(p.theta_abs_a, p.theta_rel * np.nan_to_num(ref))
    valid = ~np.isnan(di)
    dip = valid & (np.nan_to_num(di) <= -theta)
    rise = valid & (np.nan_to_num(di) >= theta)
    out = {}
    for name, mask in (("dip", dip), ("rise", rise)):
        ok = run_length(mask) >= n
        k = first_index(ok)
        out[name + "_t_s"] = None if k is None else i_adc.t0_s + (k + 1) * i_adc.dt_s
        out[name + "_ok"] = ok
    out["min_di_a"] = float(np.nanmin(di)) if valid.any() else 0.0
    out["max_di_a"] = float(np.nanmax(di)) if valid.any() else 0.0
    return out


def reversal_detector(i_adc: Signal, p: ReversalParams = ReversalParams()) -> dict:
    n = int(round(p.persist_s / i_adc.dt_s))
    ok = run_length(i_adc.samples <= p.threshold_a) >= n
    k = first_index(ok)
    return {"t_s": None if k is None else i_adc.t0_s + (k + 1) * i_adc.dt_s, "ok": ok,
            "min_i_a": float(i_adc.samples.min())}


# ----------------------------------------------------------------------------------------------
# (c) HF band channel 30-100 kHz — SYNTHETIC inputs only
# ----------------------------------------------------------------------------------------------
@dataclass(frozen=True)
class HFParams:
    f_lo_hz: float = 30e3
    f_hi_hz: float = 100e3
    order: int = 4
    frame_s: float = 1e-3
    theta_a: float = 0.05         # in-band rms per frame
    noise_rms_a: float = 0.005    # HF sensor noise floor, in-band rms (ASSUMED)
    suspect_k: int = 4
    suspect_m: int = 10
    trip_k: int = 16
    trip_m: int = 20
    corr_k: int = 8               # corroborated trip (needs a DC step flag within corr_window_s)
    corr_m: int = 10
    corr_window_s: float = 0.5


def _bandpass_sos(p: HFParams, fs: float):
    return sps.butter(p.order, [p.f_lo_hz, p.f_hi_hz], btype="bandpass", fs=fs, output="sos")


def hf_band_channel(sig: Signal, p: HFParams = HFParams(), seed: int = 0) -> dict:
    """Band-pass + frame-rms envelope + K-of-M persistence.  Refuses non-SYNTHETIC inputs."""
    if SYNTHETIC not in sig.labels:
        raise SyntheticLabelError(
            "HF channel accepts only SYNTHETIC-labelled waveforms: the ngspice arc model has no HF physics")
    fs = 1.0 / sig.dt_s
    if fs < 4.0 * p.f_hi_hz:
        raise ValueError("sample rate too low for the HF band")
    rng = np.random.default_rng(seed)
    sigma = p.noise_rms_a / math.sqrt(2.0 * (p.f_hi_hz - p.f_lo_hz) / fs)
    x = sig.samples + rng.normal(0.0, sigma, sig.n)
    sos = _bandpass_sos(p, fs)
    y, _ = sps.sosfilt(sos, x, zi=sps.sosfilt_zi(sos) * x[0])
    fn = int(round(p.frame_s * fs))
    nf = sig.n // fn
    env = np.sqrt(np.mean(y[: nf * fn].reshape(nf, fn) ** 2, axis=1))
    above = env >= p.theta_a
    t_frame_end = sig.t0_s + (np.arange(nf) + 1) * p.frame_s
    res = {"t_frame_end_s": t_frame_end, "env_a": env, "above": above,
           "suspect_ok": k_of_m(above, p.suspect_k, p.suspect_m),
           "trip_ok": k_of_m(above, p.trip_k, p.trip_m),
           "corr_ok": k_of_m(above, p.corr_k, p.corr_m),
           "max_env_a": float(env.max()) if nf else 0.0,
           "frames_above": int(above.sum())}
    for key in ("suspect", "trip", "corr"):
        k = first_index(res[key + "_ok"])
        res[key + "_t_s"] = None if k is None else float(t_frame_end[k])
    return res


def synthetic_arc_hf(n: int, dt_s: float, t_on_s: float, inband_rms_a: float, seed: int,
                     t_off_s: float | None = None, p: HFParams = HFParams()) -> Signal:
    """Gated band-limited Gaussian noise, normalised to a target 30-100 kHz rms.  SYNTHETIC: it is
    NOT an arc model; amplitude, spectrum and statistics are ASSUMED."""
    fs = 1.0 / dt_s
    rng = np.random.default_rng(seed)
    s = sps.sosfilt(sps.butter(2, [10e3, 300e3], btype="bandpass", fs=fs, output="sos"), rng.normal(0, 1, n))
    inb = sps.sosfilt(_bandpass_sos(p, fs), s)
    s *= inband_rms_a / float(np.sqrt(np.mean(inb[n // 10:] ** 2)))
    t = np.arange(n) * dt_s
    gate = (t >= t_on_s) & (t < (np.inf if t_off_s is None else t_off_s))
    return Signal(s * gate, dt_s, {SYNTHETIC, "SYNTHETIC_ARC_HF_NOT_PHYSICS"})


# === PART B ===

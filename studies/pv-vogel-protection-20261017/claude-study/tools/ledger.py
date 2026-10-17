"""Versioned, append-only Kuiper identity ledger for the cycle-1 physical scenarios.

Phase 0 keys 1..2560 (studies/pv-vogel-protection-20261017/vogel_study.py) are frozen.
Family `cycle1-physical-v1` starts at key 2561 and is assigned in the deterministic order
produced by `enumerate_cycle1()`.  Re-running this script must reproduce the same ledger
byte-for-byte; a change in enumeration order is a ledger violation (test_ledger.py).

The Kuiper address law is reproduced exactly from
Ventusltd/globalgrid2050 testcode/202609151339/lib.mjs (commit da7d8f6e, read-only):
    GOLDEN = pi*(3-sqrt(5)); r = sqrt(key); theta = key*GOLDEN; x = r cos theta; y = r sin theta
It is an address. It carries no physical, statistical or causal meaning.
"""
import hashlib
import json
import math
import sys
from pathlib import Path

GOLDEN = math.pi * (3 - math.sqrt(5))
PHASE0_LAST_KEY = 2560
FAMILY = "cycle1-physical-v1"
HERE = Path(__file__).resolve().parent
LEDGER = HERE.parent / "experiments" / "scenario-ledger.json"


MAX_SAFE_KEY = 9007199254740991  # Number.MAX_SAFE_INTEGER, the bound lib.mjs parseKey enforces


def kuiper_xy(key: int):
    if type(key) is not int or key < 1 or key > MAX_SAFE_KEY:
        raise ValueError("Kuiper key must be an integer in 1..2^53-1 (lib.mjs parseKey bound)")
    r, t = math.sqrt(key), key * GOLDEN
    return r * math.cos(t), r * math.sin(t)


# ---- Kuiper CORE placement law (live www.globalgrid2050.com/kuiper/), reproduced exactly ----
# Source: Ventusltd/globalgrid2050 commit da7d8f6e6a7806ad5039701f5c86637d84be0704,
# kuiper/releases/202609192301-kuiper-shell/index.html  (function keyPlace, line 566):
#     m = Math.imul((k % 2^32) >>> 0, G32) >>> 0 ; theta = 2*pi*m/2^32 ; r = sqrt(k + 0.5)
# with G32 = 2654435769 (floor(2^32/phi)). Same law in kuiper-belt cosmos/wafer-meta.json
# ("r = sqrt(key), theta = 2 pi frac(key x 2654435769 / 2^32)"). The 32-bit wrap is part of the law.
G32 = 2654435769
CORE_LAW = "r = sqrt(key + 0.5); theta = 2*pi*((key mod 2^32)*G32 mod 2^32)/2^32; G32 = 2654435769  [address only]"


def kuiper_core_xy(key: int):
    if type(key) is not int or key < 0 or key > MAX_SAFE_KEY:
        raise ValueError("Kuiper core key must be an integer in 0..2^53-1")
    m = ((key % 4294967296) * G32) % 4294967296
    theta = 2.0 * math.pi * m / 4294967296.0
    r = math.sqrt(key + 0.5)
    return r * math.cos(theta), r * math.sin(theta)


def enumerate_cycle1():
    """Deterministic enumeration of cycle-1 scenario identities (order is permanent)."""
    rows = []
    # C1 — module internal series arc
    for prot in ("P0", "P1", "P1b", "P2", "P2b", "P3"):
        for g in (1000, 500, 200):
            for tc in (-10, 25, 70):
                for gap in (1.0, 3.0, 5.0):
                    rows.append({
                        "scenario_id": f"C1-{prot}-G{g}-T{tc:+d}-GAP{gap:g}",
                        "case": "C1", "protection": prot,
                        "variants": {"irradiance_w_per_m2": g, "cell_temp_c": tc, "arc_gap_mm": gap},
                        "parent_phase0_label": "internal_series_arc",
                    })
    # C2 — external parallel arc (far / near), inverter architecture, irradiance incl. night
    for loc in ("far", "near"):
        for prot in ("P0", "P1", "P2", "P2b", "P3"):
            for inv in ("V_BOOST", "V_DIRECTBUS"):
                for g in (1000, 500, 0):
                    for gap in (1.0, 3.0, 5.0):
                        rows.append({
                            "scenario_id": f"C2{loc}-{prot}-{inv}-G{g}-GAP{gap:g}",
                            "case": "C2", "protection": prot,
                            "variants": {"location": loc, "inverter": inv, "irradiance_w_per_m2": g, "arc_gap_mm": gap},
                            "parent_phase0_label": "parallel_arc",
                        })
    # C3 — hot connector, no arc
    for prot in ("P0", "P1", "P1b", "P2", "P2b"):
        for r in (0.05, 0.2, 1.0):
            for g in (1000, 500):
                rows.append({
                    "scenario_id": f"C3-{prot}-R{r:g}-G{g}",
                    "case": "C3", "protection": prot,
                    "variants": {"connector_r_ohm": r, "irradiance_w_per_m2": g},
                    "parent_phase0_label": "high_resistance_hot_connector",
                })
    # Adversarial counterexamples (master brief section 6) — one identity each; physics added by workers
    adversarial = [
        ("ADV-series-arc-upstream-of-SW-M-OUT", "internal_series_arc"),
        ("ADV-series-arc-downstream-of-SW-M-OUT", "external_connector_series_arc"),
        ("ADV-parallel-fault-near-end-bolted", "parallel_arc"),
        ("ADV-parallel-fault-far-end-bolted", "parallel_arc"),
        ("ADV-first-earth-fault-floating", "insulation_or_earth_fault"),
        ("ADV-second-earth-fault-floating", "insulation_or_earth_fault"),
        ("ADV-first-earth-fault-bonded-frame", "insulation_or_earth_fault"),
        ("ADV-night-backfeed-into-string", "reverse_feed"),
        ("ADV-reverse-polarity-connection", "reverse_feed"),
        ("ADV-shorted-bypass-diode", "internal_series_arc"),
        ("ADV-open-bypass-diode-shaded-substring", "internal_series_arc"),
        ("ADV-body-diode-feed-one-switch-off", "switch_failed_short"),
        ("ADV-body-diode-feed-both-switches-off", "switch_failed_short"),
        ("ADV-module-fault-plus-gate-supply-lost", "control_supply_lost"),
        ("ADV-switch-failed-short-with-series-arc", "switch_failed_short"),
        ("ADV-switch-failed-open-nuisance", "switch_failed_open"),
        ("ADV-hot-connector-no-hf-signature", "high_resistance_hot_connector"),
        ("ADV-wet-connector-leakage", "insulation_or_earth_fault"),
        ("ADV-surge-8-20us-on-string", "benign_inverter_or_mppt_noise"),
        ("ADV-partial-shade-step", "benign_inverter_or_mppt_noise"),
        ("ADV-benign-mppt-hf-transient", "benign_inverter_or_mppt_noise"),
        ("ADV-cold-voc-max-irradiance", "switch_failed_open"),
        ("ADV-control-latency-shorter-than-wave-travel", "parallel_arc"),
        ("ADV-fail-open-diagnostic", "switch_failed_open"),
        ("ADV-fail-short-diagnostic", "switch_failed_short"),
        ("ADV-reset-restart-into-persistent-arc", "internal_series_arc"),
        ("ADV-remote-field-voltage-persistence-after-trip", "parallel_arc"),
    ]
    for sid, parent in adversarial:
        rows.append({"scenario_id": sid, "case": "ADV", "protection": "ALL", "variants": {}, "parent_phase0_label": parent})
    return rows


def build():
    rows = enumerate_cycle1()
    ledger = []
    for i, row in enumerate(rows):
        key = PHASE0_LAST_KEY + 1 + i
        x, y = kuiper_xy(key)
        cx, cy = kuiper_core_xy(key)
        ledger.append({**row, "key": key, "family": FAMILY, "kuiper_xy": [round(x, 8), round(y, 8)],
                       "kuiper_core_xy": [round(cx, 8), round(cy, 8)],
                       "model_revision": "cycle1-v1", "evidence_links": []})
    ids = [r["scenario_id"] for r in ledger]
    assert len(ids) == len(set(ids)), "duplicate scenario_id"
    return {
        "ledger_version": 2,
        "ledger_changelog": [
            "v1 2026-10-17: family cycle1-physical-v1 keys 2561..2959 with kuiper_xy (Line Wafer law); entries sha256 218b25d9293526fbe38d4430e2db556d5a833bf6b0f44c38a46a288d6bfec6b3",
            "v2 2026-10-17: added kuiper_core_xy (live Kuiper core law, keyPlace) to every entry; keys, scenario_ids and kuiper_xy unchanged",
        ],
        "core_address_law": CORE_LAW,
        "core_law_source": "Ventusltd/globalgrid2050@da7d8f6e kuiper/releases/202609192301-kuiper-shell/index.html keyPlace; kuiper-belt@40df5a3e cosmos/wafer-meta.json law",
        "family": FAMILY,
        "first_key": PHASE0_LAST_KEY + 1,
        "last_key": PHASE0_LAST_KEY + len(ledger),
        "count": len(ledger),
        "phase0_frozen_keys": [1, PHASE0_LAST_KEY],
        "address_law": "r=sqrt(key); theta=key*pi*(3-sqrt(5)); x=r*cos(theta); y=r*sin(theta)  [Line Wafer law, lib.mjs; address only]",
        "append_only_rule": "new identities are appended with the next key; existing rows are never reordered, renumbered or deleted",
        "entries": ledger,
    }


def digest(obj) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


if __name__ == "__main__":
    led = build()
    led["entries_sha256"] = digest(led["entries"])
    if "--check" in sys.argv:
        on_disk = json.loads(LEDGER.read_text())
        ok = on_disk["entries_sha256"] == led["entries_sha256"]
        print("ledger", "MATCHES" if ok else "MISMATCH", led["entries_sha256"])
        sys.exit(0 if ok else 1)
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    LEDGER.write_text(json.dumps(led, indent=1) + "\n")
    print("wrote", LEDGER, "entries", led["count"], "keys", led["first_key"], "..", led["last_key"], "sha256", led["entries_sha256"])

#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from v11_simulation.model import canonical_json, load_reference_block, simulate_comparison


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the V11 24-string reference inverter-block simulation")
    parser.add_argument("--reference", type=Path, default=ROOT / "reference" / "lab_inverter_block_24_strings.json")
    parser.add_argument("--overrides", default="{}", help="JSON object of simulation overrides")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = simulate_comparison(load_reference_block(args.reference), json.loads(args.overrides))
    text = canonical_json(result) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

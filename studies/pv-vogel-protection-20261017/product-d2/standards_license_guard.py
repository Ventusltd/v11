"""Conservative public V11 release guard for obviously restricted IEC material.

NOT a substitute for manual copyright/licence clearance. It checks filenames and
distinctive document watermarks, not semantic similarities or paraphrases.
Does NOT need access to and MUST NOT read supplied licensed IEC publications.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import re
import sys

PUBLIC_TEXT_EXTENSIONS={".md",".txt",".csv",".json",".cir",".log",".py",
                         ".yaml",".yml",".rst",".html",".xml",".spice"}
RESTRICTED_EXTENSIONS={".pdf",".png",".jpg",".jpeg",".tiff",".tif",".webp"}
RESTRICTED_NAMES=re.compile(
    r"(?:^|[_\-\s])(?:iec|bs[\s_\-]*en[\s_\-]*iec)\s*[_\-\s]*"
    r"(?:62548|62738|60664|61730)\b",re.I)
# Encode short watermark clues without shipping an actual watermark text block.
MARKER1="Cus"+"tomer:"
MARKER2="Lic"+"ence:"
MARKER3="Order"+" No.:"
BODY_MARKERS=[
    re.compile(r"\bthis\s+publication\s+is\s+copyright\s+protected\b",re.I),
    re.compile(r"\bAll\s+rights\s+reserved\.\s+Unless\s+otherwise\s+specified\b",re.I),
]

def problems(directory:Path):
    found=[]
    for p in sorted(directory.rglob("*")):
        if not p.is_file():
            continue
        if p.name=="standards_license_guard.py" or p.name=="test_standards_license_guard.py":
            continue
        if p.suffix.lower() in RESTRICTED_EXTENSIONS and RESTRICTED_NAMES.search(p.name):
            found.append((p.relative_to(directory).as_posix(),"suspected restricted IEC document or page image"))
            continue
        if p.suffix.lower() not in PUBLIC_TEXT_EXTENSIONS:
            continue
        if p.stat().st_size>3_000_000:
            found.append((p.relative_to(directory).as_posix(),"oversize public text file requires manual review"))
            continue
        try:
            data=p.read_text(encoding="utf8")
        except UnicodeDecodeError:
            found.append((p.relative_to(directory).as_posix(),"text extension with non-UTF8 data requires review"))
            continue
        # Check telltale full licensed-standard customer footer patterns.
        if all(x in data for x in (MARKER1,MARKER2,MARKER3)):
            found.append((p.relative_to(directory).as_posix(),"potential IEC licensed single-user watermark"))
        elif any(x.search(data) for x in BODY_MARKERS):
            found.append((p.relative_to(directory).as_posix(),"potential copied IEC copyright notice"))
    return found

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("directory",nargs="?",default=".")
    args=parser.parse_args()
    root=Path(args.directory)
    if not root.is_dir():
        raise SystemExit("Missing product research folder")
    issues=problems(root)
    if issues:
        for file,reason in issues:
            print(f"REVIEW_REQUIRED: {file}: {reason}")
        raise SystemExit(1)
    print("PASS: no obvious restricted IEC files/watermarks in D2 public research folder.")
    print("LIMITATION: manual copyright/licence clearance remains mandatory.")
if __name__=="__main__":
    main()

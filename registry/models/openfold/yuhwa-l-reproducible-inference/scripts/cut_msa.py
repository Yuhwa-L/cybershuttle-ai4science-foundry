#!/usr/bin/env python3
"""Copy a precomputed OpenFold alignment folder, keeping only the first N sequences.

Each of the three MSA files (bfd_uniref_hits.a3m, uniref90_hits.sto,
mgnify_hits.sto) keeps its first N sequences, the query included, so N=1 means
single-sequence input. The template search result (hhsearch_output.hhr) is
copied unchanged, so only the MSA changes.

Usage:
  python scripts/cut_msa.py SRC_DIR DST_DIR N
  e.g. python scripts/cut_msa.py length-series/alignments/9OUF_A msa-depth/alignments-8/9OUF_A 8
"""

import shutil
import sys
from pathlib import Path


def cut_a3m(src, dst, n):
    kept, out = 0, []
    for line in src.read_text().splitlines(keepends=True):
        if line.startswith(">"):
            kept += 1
            if kept > n:
                break
        out.append(line)
    dst.write_text("".join(out))
    return kept if kept <= n else n


def cut_sto(src, dst, n):
    lines = src.read_text().splitlines(keepends=True)
    names = []  # sequence names in order of first appearance
    for line in lines:
        if line.strip() and not line.startswith(("#", "//")):
            name = line.split()[0]
            if name not in names:
                names.append(name)
    keep = set(names[:n])
    out = []
    for line in lines:
        parts = line.split()
        if line.startswith(("#=GS", "#=GR")):
            if len(parts) > 1 and parts[1] in keep:
                out.append(line)
        elif line.startswith("#=GC"):
            continue  # column annotations describe the full alignment
        elif line.strip() and not line.startswith(("#", "//")):
            if parts[0] in keep:
                out.append(line)
        else:
            out.append(line)
    dst.write_text("".join(out))
    return len(keep)


def main():
    src, dst, n = Path(sys.argv[1]), Path(sys.argv[2]), int(sys.argv[3])
    dst.mkdir(parents=True, exist_ok=True)
    for f in sorted(src.iterdir()):
        if f.suffix == ".a3m":
            k = cut_a3m(f, dst / f.name, n)
        elif f.suffix == ".sto":
            k = cut_sto(f, dst / f.name, n)
        else:
            shutil.copy(f, dst / f.name)
            continue
        print(f"{dst.name}/{f.name}: kept {k} sequences")


if __name__ == "__main__":
    main()

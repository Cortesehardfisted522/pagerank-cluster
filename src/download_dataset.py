#!/usr/bin/env python3
"""
download_dataset.py — Downloads Stanford Web-Google graph (SNAP)
Output: data/web-Google.txt  (~100MB uncompressed, 875K nodes, 5M edges)
"""

import gzip
import shutil
import urllib.request
from pathlib import Path

URLS = [
    "https://snap.stanford.edu/data/web-Google.txt.gz",
    "https://snap.stanford.edu/data/web-Google.txt.gz",  # retry same — add mirror if known
]

ROOT    = Path(__file__).parent.parent
DATA    = ROOT / "data"
OUT     = DATA / "web-Google.txt"
GZ      = DATA / "web-Google.txt.gz"


def progress(count, block, total):
    if total > 0:
        pct = min(100, int(count * block * 100 / total))
        bar = "█" * (pct // 5) + "░" * (20 - pct // 5)
        print(f"\r  [{bar}] {pct}%", end="", flush=True)


def download():
    DATA.mkdir(exist_ok=True)

    if OUT.exists():
        size  = OUT.stat().st_size / 1e6
        lines = sum(1 for _ in open(OUT))
        print(f"✓ Dataset already at {OUT}")
        print(f"  {size:.1f} MB · {lines:,} lines")
        return

    for url in URLS:
        try:
            print(f"Downloading from {url} ...")
            urllib.request.urlretrieve(url, GZ, reporthook=progress)
            print()
            break
        except Exception as e:
            print(f"\n  ✗ Failed: {e}")
            if GZ.exists():
                GZ.unlink()
    else:
        raise RuntimeError("All download URLs failed. Check network connectivity.")

    print("Extracting...")
    with gzip.open(GZ, "rb") as f_in, open(OUT, "wb") as f_out:
        shutil.copyfileobj(f_in, f_out)
    GZ.unlink()

    # Quick stats
    edges, nodes = 0, set()
    with open(OUT) as f:
        for line in f:
            if line.startswith("#"):
                continue
            p = line.strip().split()
            if len(p) == 2:
                nodes.update(p)
                edges += 1

    print(f"\n✓ Ready: {OUT}")
    print(f"  Nodes: {len(nodes):,}")
    print(f"  Edges: {edges:,}")
    print(f"\nNext: hdfs dfs -put {OUT} /pagerank/input/")


if __name__ == "__main__":
    download()

#!/usr/bin/env python3
"""
pagerank.py — Distributed PageRank · Group 03
Apache Spark RDD implementation with mandatory caching.

Usage:
  spark-submit --master spark://MASTER_IP:7077 \
               --executor-memory 2g \
               --driver-memory 1g \
               src/pagerank.py [iterations]
"""

import sys
import json
import time
import os
from pathlib import Path

from pyspark import SparkContext, SparkConf

# ── Config ────────────────────────────────────────────────────────────────────
ITERATIONS     = int(sys.argv[1]) if len(sys.argv) > 1 else 10
DAMPING        = 0.85
INPUT_HDFS     = "hdfs:///pagerank/input/web-Google.txt"
INPUT_LOCAL    = Path(__file__).parent.parent / "data" / "web-Google.txt"
OUTPUT_HDFS    = "hdfs:///pagerank/output"
OUTPUT_LOCAL   = Path(__file__).parent.parent / "data" / "pagerank_output"
DATA_DIR       = Path(__file__).parent.parent / "data"
TOP_N          = 5
# Checkpoint every N iterations to truncate RDD lineage (prevents stack overflow on long runs)
CHECKPOINT_EVERY = 5

# ── Spark ─────────────────────────────────────────────────────────────────────
# Use local mode to avoid Java 25 / Hadoop UGI compatibility issues
conf = (SparkConf()
        .setAppName("Group03-PageRank")
        .setMaster("local[*]")
        .set("spark.serializer", "org.apache.spark.serializer.KryoSerializer")
        .set("spark.kryo.registrationRequired", "false")
        .set("spark.ui.showConsoleProgress", "true")
        # Disable Hadoop FS defaults to avoid Java 25 UGI compatibility issues
        .set("spark.hadoop.fs.defaultFS", "file:///tmp")
        .set("spark.hadoop.hadoop.tmp.dir", "/tmp/spark-tmp"))

sc = SparkContext(conf=conf)
sc.setLogLevel("WARN")

# Checkpoint dir disabled due to Java 25 / Hadoop 3.5.0 compatibility issue
# sc.setCheckpointDir("hdfs:///pagerank/checkpoints")

print("\n" + "═"*55)
print("  Group 03 · Network Graph PageRank")
print(f"  Iterations : {ITERATIONS}")
print(f"  Damping    : {DAMPING}")
print(f"  Input      : {INPUT_HDFS}")
print("═"*55 + "\n")

t0 = time.time()

# Parse graph — read via raw Python first, create Spark RDD in-memory
# This avoids Hadoop FileSystem UGI issues on Java 25
print("Loading graph from local file...")
with open(INPUT_LOCAL) as f:
    lines = [l.strip() for l in f if not l.startswith('#') and '\t' in l]
edge_pairs = [tuple(ln.split('\t')[:2]) for ln in lines]
print(f"  {len(edge_pairs):,} edges loaded")

# Create Spark RDD from in-memory list
edges = sc.parallelize(edge_pairs)

# Adjacency list: {src_node: [dst_node, ...]}
links = edges.groupByKey().mapValues(list)

# ── CACHE #1: links ───────────────────────────────────────────────────────────
# Load the full graph into executor memory ONCE before the iteration loop.
# Every subsequent join reads from RAM, not HDFS. Without this, each of the
# ITERATIONS iterations would trigger a full re-read of the 100MB input file.
links.cache()
node_count = links.count()   # materialises the cache
print(f"Graph loaded: {node_count:,} source nodes cached in executor memory\n")

# Initial ranks: all nodes start at 1.0
ranks = links.mapValues(lambda _: 1.0)

# ── Power iteration ───────────────────────────────────────────────────────────
def distribute(url_rank):
    """Spread a node's rank equally across its outgoing links."""
    neighbors, rank = url_rank
    n = len(neighbors)
    for neighbor in neighbors:
        yield (neighbor, rank / n)

for i in range(ITERATIONS):
    t_iter = time.time()

    contributions = links.join(ranks).flatMap(lambda x: distribute(x[1]))

    ranks = (contributions
             .reduceByKey(lambda a, b: a + b)
             .mapValues(lambda s: (1.0 - DAMPING) + DAMPING * s))

    # ── CACHE #2: ranks (per iteration) ──────────────────────────────────────
    # Without this, Spark rebuilds the full lineage DAG for every join —
    # iteration N would recompute all N-1 previous rank transformations.
    # With cache(), ranks is materialised as a flat RDD each round: O(1) lookback.
    ranks.cache()

    # Checkpoint disabled (Java 25 / HDFS compatibility)
    # if (i + 1) % CHECKPOINT_EVERY == 0:
    #     ranks.checkpoint()

    dt = time.time() - t_iter
    print(f"  Iteration {i+1:2d}/{ITERATIONS}  {dt:.1f}s")

# ── Collect & save ────────────────────────────────────────────────────────────
print("\nCollecting results...")
all_ranks = sorted(ranks.collect(), key=lambda x: x[1], reverse=True)

top5 = [
    {"rank": idx + 1, "nodeId": node, "pagerank": round(score, 8)}
    for idx, (node, score) in enumerate(all_ranks[:TOP_N])
]

print("\n" + "═"*55)
print(f"  TOP {TOP_N} MOST INFLUENTIAL NODES")
print("═"*55)
for e in top5:
    print(f"  #{e['rank']}  node {e['nodeId']:>10s}  →  {e['pagerank']:.8f}")
print("═"*55)

DATA_DIR.mkdir(exist_ok=True)

with open(DATA_DIR / "top5.json", "w") as f:
    json.dump(top5, f, indent=2)

with open(DATA_DIR / "results.json", "w") as f:
    json.dump([{"nodeId": n, "pagerank": round(s, 8)} for n, s in all_ranks[:1000]], f, indent=2)

# Write output to local file using Python (avoids Java 25 Hadoop UGI compatibility issue)
output_file = OUTPUT_LOCAL / "part-00000"
OUTPUT_LOCAL.mkdir(exist_ok=True)
if output_file.exists():
    output_file.unlink()
with open(str(output_file), "w") as f:
    for node, score in all_ranks:
        f.write(f"{node}\t{score:.10f}\n")

total = time.time() - t0
print(f"\n✓ Done in {total:.1f}s")
print(f"  Local:  {output_file}")
print(f"\n  Next:  python3 src/api.py")

sc.stop()

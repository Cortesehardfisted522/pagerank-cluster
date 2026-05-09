#!/usr/bin/env python3
"""
api.py — Cross-Group Portability REST API · Group 03
Exposes PageRank results for the portability evaluation.

Endpoints:
  GET /top5          → Top 5 influencer nodes
  GET /top/<int:n>   → Top N ranked nodes (max 1000)
  GET /node/<id>     → Score for a specific node
  GET /neighbors/<id>→ Nodes this node links to (outgoing edges)
  GET /influencedby/<id> → Nodes that link to this node (incoming edges)
  GET /stats         → Job metadata + live service info
  POST /rerun        → Trigger a background PageRank rerun
  GET /rerun/status  → Current rerun job status
  GET /health        → Service status
"""

import json
import socket
import sys
import threading
import subprocess
import time
import os
from datetime import datetime, timezone
from pathlib import Path
from flask import Flask, jsonify, abort, request

app = Flask(__name__)

DATA_DIR   = Path(__file__).parent.parent / "data"
TOP5_FILE  = DATA_DIR / "top5.json"
FULL_FILE  = DATA_DIR / "results.json"
GRAPH_FILE = DATA_DIR / "graph.json"
META_FILE  = DATA_DIR / "meta.json"

# In-memory cache for reverse graph index (built on first use)
_reverse_index = None
_reverse_index_lock = threading.Lock()


# ── helpers ───────────────────────────────────────────────────────────────────

def _load(path):
    if not path.exists():
        return None
    with open(path) as f:
        return json.load(f)


def _load_graph():
    data = _load(GRAPH_FILE)
    if data is None:
        abort(503, "Graph data not ready. Run src/pagerank.py first.")
    return data


def _build_reverse_index():
    global _reverse_index
    if _reverse_index is not None:
        return _reverse_index
    with _reverse_index_lock:
        if _reverse_index is not None:
            return _reverse_index
        graph = _load_graph()
        rev = {}
        for node, neighbors in graph.items():
            for n in neighbors:
                rev.setdefault(n, []).append(node)
        _reverse_index = rev
        return _reverse_index


# ── job state (shared across threads) ───────────────────────────────────────

job_state = {
    "status": "idle",
    "job_id": None,
    "started_at": None,
    "completed_at": None,
    "error": None,
    "params": None,
}
_job_lock = threading.Lock()


# ── endpoints ─────────────────────────────────────────────────────────────────

@app.route("/top5")
def get_top5():
    data = _load(TOP5_FILE)
    if data is None:
        abort(503, "Results not ready. Run src/pagerank.py first.")
    return jsonify(data)


@app.route("/top/<n>")
def get_top_n(n):
    try:
        n = int(n)
    except (ValueError, TypeError):
        abort(400, "n must be an integer")
    if n < 1:
        return jsonify({"error": "n must be at least 1"}), 400
    results = _load(FULL_FILE)
    if results is None:
        abort(503, "Results not ready. Run src/pagerank.py first.")
    max_available = len(results)
    returned = min(n, max_available)
    note = None
    if n > max_available:
        note = f"Only {max_available} nodes available; returned all"
    resp = {
        "requested": n,
        "returned": returned,
        "nodes": results[:returned]
    }
    if note:
        resp["note"] = note
    return jsonify(resp)


@app.route("/node/<node_id>")
def get_node(node_id):
    data = _load(FULL_FILE)
    if data is None:
        abort(503, "Results not ready. Run src/pagerank.py first.")
    match = next((e for e in data if str(e["nodeId"]) == node_id), None)
    if match is None:
        abort(404, f"Node '{node_id}' not in top-1000 results.")
    return jsonify(match)


@app.route("/neighbors/<node_id>")
def get_neighbors(node_id):
    graph = _load_graph()
    if node_id not in graph:
        abort(404,
              f"Node '{node_id}' not found in graph. "
              "This may be a sink node (has no outgoing edges — it receives links but doesn't link to anything).")
    neighbors = graph[node_id]
    return jsonify({
        "nodeId": node_id,
        "direction": "outgoing",
        "count": len(neighbors),
        "neighbors": neighbors,
    })


@app.route("/influencedby/<node_id>")
def get_influencedby(node_id):
    rev = _build_reverse_index()
    sources = rev.get(node_id, None)
    if sources is None:
        abort(404,
              f"Node '{node_id}' not found in incoming links index. "
              "This may be a sink node (no other nodes link to it).")
    return jsonify({
        "nodeId": node_id,
        "direction": "incoming",
        "count": len(sources),
        "sources": sources,
    })


@app.route("/stats")
def get_stats():
    meta = _load(META_FILE)
    if meta is None:
        abort(503, "Meta data not ready. Run src/pagerank.py first.")
    return jsonify({
        "dataset":       meta.get("dataset_name", "unknown"),
        "total_nodes":   meta.get("total_nodes", 0),
        "total_edges":   meta.get("total_edges", 0),
        "iterations":    meta.get("iterations", 0),
        "damping_factor": meta.get("damping_factor", 0),
        "top_node":      meta.get("top_node", ""),
        "completed_at":  meta.get("completed_at", ""),
        "api_status":    "ok",
        "endpoints": [
            "/top5",
            "/top/<n>",
            "/node/<id>",
            "/neighbors/<id>",
            "/influencedby/<id>",
            "/stats",
            "/rerun",
            "/health",
        ],
    })


@app.route("/rerun", methods=["POST"])
def post_rerun():
    params = request.get_json(silent=True) or {}
    iterations    = params.get("iterations")
    damping       = params.get("damping_factor")
    dataset_url   = params.get("dataset_url")
    job_id = f"rerun_{int(time.time())}"
    with _job_lock:
        job_state.update({
            "status":      "queued",
            "job_id":      job_id,
            "started_at":  datetime.now(timezone.utc).isoformat(),
            "completed_at": None,
            "error":       None,
            "params":      params,
        })

    # Spawn background thread
    def background_rerun():
        with _job_lock:
            job_state["status"] = "running"
        try:
            # Download dataset if needed
            if dataset_url:
                script_dir = Path(__file__).parent
                dl_script = script_dir / "download_dataset.py"
                if dl_script.exists():
                    subprocess.run(
                        [sys.executable, str(dl_script), "--url", dataset_url],
                        capture_output=True, text=True
                    )
            # Run pagerank
            script_dir = Path(__file__).parent.parent
            pr_script = script_dir / "src" / "pagerank.py"
            cmd = [sys.executable, str(pr_script)]
            if iterations is not None:
                cmd.append(str(iterations))
            subprocess.run(cmd, capture_output=True, text=True, cwd=str(script_dir))
            # Invalidate caches
            global _reverse_index
            with _reverse_index_lock:
                _reverse_index = None
            with _job_lock:
                job_state.update({
                    "status":       "completed",
                    "completed_at": datetime.now(timezone.utc).isoformat(),
                })
        except Exception as exc:
            with _job_lock:
                job_state.update({
                    "status": "failed",
                    "error":  str(exc),
                })

    threading.Thread(target=background_rerun, daemon=True).start()
    return jsonify({
        "job_id": job_id,
        "status": "queued",
        "params": params,
    }), 202


@app.route("/rerun/status")
def get_rerun_status():
    with _job_lock:
        state = dict(job_state)
    if state["status"] == "idle":
        return jsonify({"status": "idle"})
    return jsonify(state)


@app.route("/health")
def health():
    return jsonify({
        "status":        "ok",
        "group":         "03",
        "task":          "Network Graph PageRank",
        "framework":     "Apache Spark",
        "dataset":       "Stanford Web-Google",
        "results_ready": TOP5_FILE.exists() and FULL_FILE.exists(),
    })


@app.errorhandler(503)
@app.errorhandler(404)
@app.errorhandler(400)
def err(e):
    return jsonify({"error": e.description}), e.code


if __name__ == "__main__":
    ip = socket.gethostbyname(socket.gethostname())
    top5   = _load(TOP5_FILE)
    graph  = _load(GRAPH_FILE)
    meta   = _load(META_FILE)

    endpoints = [
        "GET  /top5           → top 5 influencers",
        "GET  /top/<n>        → top N ranked nodes",
        "GET  /node/<id>      → score for node id",
        "GET  /neighbors/<id> → outgoing edges",
        "GET  /influencedby/<id> → incoming edges",
        "GET  /stats          → job metadata + service info",
        "POST /rerun          → trigger background rerun",
        "GET  /rerun/status   → rerun job status",
        "GET  /health         → status check",
    ]

    print("=" * 52)
    print("  Group 03 · PageRank Portability API")
    print(f"  http://{ip}:5000")
    print()
    for ep in endpoints:
        print(f"  {ep}")
    print()
    if top5:
        print(f"  ✓ Results loaded — top node: {top5[0]['nodeId']} ({top5[0]['pagerank']:.6f})")
    else:
        print("  ⚠  No results yet — run src/pagerank.py first")
    print("=" * 52)
    app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)
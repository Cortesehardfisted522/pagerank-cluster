#!/usr/bin/env python3
"""
api.py — Cross-Group Portability REST API · Group 03
Exposes PageRank results for the portability evaluation.

Endpoints:
  GET /top5          → Top 5 influencer nodes
  GET /node/<id>     → Score for a specific node
  GET /health        → Service status
"""

import json
import socket
from pathlib import Path
from flask import Flask, jsonify, abort

app = Flask(__name__)

DATA_DIR  = Path(__file__).parent.parent / "data"
TOP5_FILE = DATA_DIR / "top5.json"
FULL_FILE = DATA_DIR / "results.json"


def _load(path):
    if not path.exists():
        return None
    with open(path) as f:
        return json.load(f)


@app.route("/top5")
def get_top5():
    data = _load(TOP5_FILE)
    if data is None:
        abort(503, "Results not ready. Run src/pagerank.py first.")
    return jsonify(data)


@app.route("/node/<node_id>")
def get_node(node_id):
    data = _load(FULL_FILE)
    if data is None:
        abort(503, "Results not ready. Run src/pagerank.py first.")
    match = next((e for e in data if str(e["nodeId"]) == node_id), None)
    if match is None:
        abort(404, f"Node '{node_id}' not in top-1000 results.")
    return jsonify(match)


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
def err(e):
    return jsonify({"error": e.description}), e.code


if __name__ == "__main__":
    ip = socket.gethostbyname(socket.gethostname())
    top5 = _load(TOP5_FILE)
    print("═" * 50)
    print("  Group 03 · PageRank Portability API")
    print(f"  http://{ip}:5000")
    print()
    print("  GET /top5          → top 5 influencers")
    print("  GET /node/<id>     → score for node id")
    print("  GET /health        → status check")
    print()
    if top5:
        print(f"  ✓ Results loaded — top node: {top5[0]['nodeId']} ({top5[0]['pagerank']:.6f})")
    else:
        print("  ⚠  No results yet — run src/pagerank.py first")
    print("═" * 50)
    app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)

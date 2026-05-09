# Network Graph PageRank — Group 03

Distributed PageRank over the [Stanford Web-Google graph](https://snap.stanford.edu/data/web-Google.html) (875 K nodes, 5 M edges) using Apache Spark and Hadoop HDFS. Exposes results through a small REST API for cross-group portability testing.

**Stack:** Python 3.8+ · Apache Spark 3.5.1 · Hadoop HDFS 3.3.6
**OS support:** macOS · Linux · Windows

---

## Quick start

```
git clone https://github.com/munimx/pagerank-cluster
cd pagerank-cluster
```

Edit `setup/config.py` and set `MASTER_IP` to the master machine's LAN IP — that is the only line you need to change.

---

## Repository layout

```
setup/
  config.py           shared config (MASTER_IP, paths, OS detection)
  setup_node.py       installs Hadoop + Spark, starts services
  register_worker.py  adds a worker IP to the cluster roster

src/
  download_dataset.py downloads datasets from SNAP
  pagerank.py         Spark RDD PageRank implementation
  api.py              Flask REST API
  generate_manual.py  generates docs/manual.html

data/
  top5.json           top-5 results
  results.json        top-1000 results
  graph.json          full adjacency list (node → [neighbors])
  meta.json           job metadata (nodes, edges, iterations, damping factor)
  pagerank_output/    all nodes, tab-separated (nodeId\tscore)
```

---

## Setup

### Master node

```bash
# 1. Find your LAN IP and set it in setup/config.py
#    macOS:   ipconfig getifaddr en0
#    Linux:   hostname -I | awk '{print $1}'
#    Windows: (Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.IPAddress -like "192.168.*" }).IPAddress

# 2. Run master setup (installs Hadoop + Spark, starts HDFS + Spark Master)
python3 setup/setup_node.py --role master

# 3. Verify — jps should show NameNode, DataNode, SecondaryNameNode, Master
jps
```

### Worker nodes

```bash
# On each worker machine — MASTER_IP in config.py must point to the master, not this machine
python3 setup/setup_node.py --role worker

# On the master — register each worker by its LAN IP
python3 setup/register_worker.py <worker_ip>
```

---

## Running PageRank

```bash
# Download and push the dataset to HDFS
python3 src/download_dataset.py
hdfs dfs -put data/web-Google.txt /pagerank/input/

# Submit the job (default: 10 iterations, damping 0.85)
spark-submit \
  --master spark://<MASTER_IP>:7077 \
  --executor-memory 2g \
  --driver-memory 1g \
  src/pagerank.py 10
```

On completion, five files are written to `data/`:
`top5.json` (top-5 ranked nodes), `results.json` (top-1000), `graph.json` (full adjacency list), `meta.json` (job metadata), and `pagerank_output/part-00000` (all nodes, tab-separated).

---

## Portability API

```bash
python3 src/api.py
```

| Endpoint | Description |
|---|---|
| `GET /health` | Service status |
| `GET /top5` | Top 5 nodes by PageRank score |
| `GET /top/<n>` | Top N nodes (1–1000, capped at available) |
| `GET /node/<id>` | Score for a specific node (top 1000 only) |
| `GET /neighbors/<id>` | Nodes this node links to (outgoing edges) |
| `GET /influencedby/<id>` | Nodes that link to this node (incoming edges) |
| `GET /stats` | Job metadata (nodes, edges, iterations, damping, timestamps) |
| `POST /rerun` | Trigger a background rerun with optional new parameters |
| `GET /rerun/status` | Current rerun job status |

The API listens on `0.0.0.0:5000`.

**Sample response — `/top5`:**

```json
[
  { "rank": 1, "nodeId": "41909",  "pagerank": 445.71778597 },
  { "rank": 2, "nodeId": "597621", "pagerank": 406.62836675 },
  { "rank": 3, "nodeId": "504140", "pagerank": 399.08930875 },
  { "rank": 4, "nodeId": "384666", "pagerank": 392.82584373 },
  { "rank": 5, "nodeId": "537039", "pagerank": 383.90912550 }
]
```

**Background rerun** — `POST /rerun` accepts optional parameters to change iterations, damping factor, or swap to a different SNAP dataset entirely:

```bash
# More iterations
curl -X POST http://localhost:5000/rerun \
  -H 'Content-Type: application/json' \
  -d '{"iterations": 15}'

# Swap to Twitter graph
curl -X POST http://localhost:5000/rerun \
  -H 'Content-Type: application/json' \
  -d '{"dataset_url": "https://snap.stanford.edu/data/twitter_combined.txt.gz"}'
```

Check status with `GET /rerun/status` — returns `idle`, `queued`, `running`, `completed`, or `failed` with timestamps.

---

## Documentation

Generate the full HTML manual (three-part: master setup, worker setup, portability test):

```bash
python3 src/generate_manual.py
python3 -m http.server 8888 --directory docs
# Open: http://localhost:8888/
```

---

## Web UIs

Once the master is running:

| UI | URL |
|---|---|
| Spark Master | `http://<MASTER_IP>:8080` |
| HDFS NameNode | `http://<MASTER_IP>:9870` |
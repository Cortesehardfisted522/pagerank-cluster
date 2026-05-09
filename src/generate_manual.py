#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate_manual.py — Produces docs/manual.html
Three-part setup manual for Group 03: Network Graph PageRank.
Audience: CS students who know terminals but have never touched Hadoop or Spark.
"""

import json
import os
from pathlib import Path
from datetime import datetime

ROOT     = Path(__file__).parent.parent
DATA_DIR = ROOT / "data"
DOCS_DIR = ROOT / "docs"
DOCS_DIR.mkdir(exist_ok=True)

top5 = []
top5_json_str = '[\n  "Run pagerank.py first to populate this"\n]'
if (DATA_DIR / "top5.json").exists():
    with open(DATA_DIR / "top5.json") as f:
        top5 = json.load(f)
    top5_json_str = json.dumps(top5, indent=2)

master_ip = os.environ.get("MASTER_IP", "192.168.1.14")
today     = datetime.now().strftime("%B %d, %Y")
top_node  = top5[0]["nodeId"] if top5 else "41909"
top_score = str(top5[0]["pagerank"]) if top5 else "445.71778597"

# ── helpers ───────────────────────────────────────────────────────────────────

def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def cb(code, lang=""):
    return (
        '<div class="code-wrap">'
        '<button class="copy-btn" aria-label="Copy code">Copy</button>'
        '<pre><code class="lang-' + lang + '">' + esc(code) + '</code></pre>'
        '</div>'
    )

def tabs(macos, linux, windows):
    return (
        '<div class="os-tabs">'
        '<div class="os-tab-bar" role="tablist">'
        '<button class="os-tab" role="tab" data-os="macos">macOS</button>'
        '<button class="os-tab" role="tab" data-os="linux">Linux</button>'
        '<button class="os-tab" role="tab" data-os="windows">Windows</button>'
        '</div>'
        '<div class="os-pane" data-os="macos">' + cb(macos, "bash") + '</div>'
        '<div class="os-pane" data-os="linux">' + cb(linux, "bash") + '</div>'
        '<div class="os-pane" data-os="windows">' + cb(windows, "powershell") + '</div>'
        '</div>'
    )

def warn(title, body):
    return (
        '<div class="callout callout-warn">'
        '<span class="callout-icon">&#9888;</span>'
        '<div><strong>' + title + '</strong>' + body + '</div>'
        '</div>'
    )

def tip(title, body):
    return (
        '<div class="callout callout-tip">'
        '<span class="callout-icon">&#128161;</span>'
        '<div><strong>' + title + '</strong>' + body + '</div>'
        '</div>'
    )

def ok(title, body):
    return (
        '<div class="callout callout-ok">'
        '<span class="callout-icon">&#10003;</span>'
        '<div><strong>' + title + '</strong>' + body + '</div>'
        '</div>'
    )

def section(id_, num, title, body):
    return (
        '<section id="' + id_ + '">'
        '<h3><span class="sec-num">' + num + '</span>' + title + '</h3>'
        + body +
        '</section>'
    )

def part_div(n, title):
    return (
        '<div class="part-divider" id="part' + str(n) + '">'
        '<div class="part-label">Part ' + str(n) + '</div>'
        '<div class="part-title">' + title + '</div>'
        '</div>'
    )

# ── top-5 results table ───────────────────────────────────────────────────────
if top5:
    rows = "".join(
        '<tr><td class="rank">#' + str(e["rank"]) + '</td>'
        '<td><code>' + str(e["nodeId"]) + '</code></td>'
        '<td class="score">' + "{:.8f}".format(e["pagerank"]) + '</td></tr>'
        for e in top5
    )
    top5_table = (
        '<table class="results-table">'
        '<thead><tr><th>Rank</th><th>Node ID</th><th>PageRank Score</th></tr></thead>'
        '<tbody>' + rows + '</tbody>'
        '</table>'
    )
else:
    top5_table = '<p class="muted">Run <code>src/pagerank.py</code> first to populate results.</p>'

# ==============================================================================
# PART 1 CONTENT
# ==============================================================================

p1_s1 = section("s1-1", "1.1", "Prerequisites",
    "<p>Before running anything, verify these three tools are installed. Every command below must succeed.</p>"
    "<h4>Python 3.8+</h4>"
    + cb("python3 --version", "bash")
    + ok("Expected output", "<p><code>Python 3.10.12</code> (or any 3.8+). If you see <em>command not found</em>, install Python from <code>python.org</code>.</p>")
    + "<h4>Java 11</h4>"
    + cb("java -version", "bash")
    + ok("Expected output", "<p><code>openjdk version &quot;11.0.22&quot; 2024-01-16</code> &mdash; the word <em>11</em> must appear. Java 17 also works.</p>")
    + "<p>If Java is missing, install it now:</p>"
    + tabs(
        "brew install openjdk@11\n# Then add to your shell profile:\nexport PATH=\"$(brew --prefix openjdk@11)/bin:$PATH\"\nsource ~/.zprofile",
        "sudo apt-get update\nsudo apt-get install -y openjdk-11-jdk",
        "winget install EclipseAdoptium.Temurin.11.JDK --silent\n# Or download the .msi from: https://adoptium.net",
    )
    + warn("Java version matters", "<p>Hadoop's startup scripts are sensitive to the Java version. Java 8 and Java 21+ both cause subtle failures. Stick to Java 11 (or 17 at most).</p>")
    + "<h4>Git</h4>"
    + cb("git --version", "bash")
    + ok("Expected output", "<p><code>git version 2.x.x</code>. If missing, install via <code>brew install git</code> (macOS), <code>sudo apt install git</code> (Linux), or from <code>git-scm.com</code> (Windows).</p>")
)

p1_s2 = section("s1-2", "1.2", "Find Your LAN IP",
    "<p>Your LAN IP is the address other machines on the same Wi-Fi will use to reach yours. It usually starts with <code>192.168.</code> or <code>10.</code>.</p>"
    + tabs(
        "ipconfig getifaddr en0\n# Expected output example:\n# 192.168.1.14",
        "hostname -I | awk '{print $1}'\n# Expected output example:\n# 192.168.1.14",
        "(Get-NetIPAddress -AddressFamily IPv4 |\n  Where-Object { $_.IPAddress -like '192.168.*' }).IPAddress\n# Expected output example:\n# 192.168.1.14",
    )
    + tip("Can't find your IP?", "<p>Make sure your machine is connected to the same Wi-Fi as the other nodes. Ethernet connections may show up on <code>en1</code> (macOS) or <code>eth0</code> (Linux) instead.</p>")
)

p1_s3 = section("s1-3", "1.3", "Configure",
    "<p>Open <code>setup/config.py</code>. There is exactly one line you need to change &mdash; <code>MASTER_IP</code>. Everything else is auto-detected.</p>"
    "<p><strong>Before</strong> (the default placeholder):</p>"
    + cb('MASTER_IP = "192.168.1.14"   # set to master laptop\'s LAN IP', "python")
    + "<p><strong>After</strong> (your actual LAN IP from Section 1.2):</p>"
    + cb('MASTER_IP = "192.168.1.42"   # your actual LAN IP here', "python")
    + warn("Set this before running anything", "<p>Every setup script imports <code>config.py</code>. If <code>MASTER_IP</code> is wrong, Hadoop and Spark will start but workers will be unable to connect &mdash; and the error messages won't point here.</p>")
    + "<p>Verify the config loads cleanly:</p>"
    + cb("python3 setup/config.py", "bash")
    + ok("Expected output",
        "<pre>OS          : Darwin\n"
        "Local IP    : 192.168.1.42\n"
        "MASTER_IP   : 192.168.1.42\n"
        "JAVA_HOME   : /opt/homebrew/opt/openjdk@11\n"
        "HADOOP_HOME : /opt/homebrew/Cellar/hadoop/3.5.0/libexec\n"
        "SPARK_HOME  : /opt/spark-3.5.1\n"
        "  [ok] Java: openjdk version \"11.0.22\" 2024-01-16</pre>"
    )
)

p1_s4 = section("s1-4", "1.4", "Run Master Setup",
    "<p>This single command installs Hadoop (a distributed filesystem) and Spark (a distributed computation engine), formats the filesystem, and starts all required services.</p>"
    + cb("python3 setup/setup_node.py --role master", "bash")
    + "<p>The script prints phases as it runs. Here is what each one means:</p>"
    "<table>"
    "<thead><tr><th>Phase printed</th><th>What is happening</th></tr></thead>"
    "<tbody>"
    "<tr><td><code>-- Java 11 --</code></td><td>Checks Java is present; installs if missing.</td></tr>"
    "<tr><td><code>-- Python dependencies --</code></td><td>Installs <code>pyspark</code>, <code>flask</code>, <code>requests</code> via pip.</td></tr>"
    "<tr><td><code>-- Hadoop 3.3.6 (master) --</code></td><td>Downloads ~650 MB Hadoop archive and extracts it. Writes XML config files pointing at your <code>MASTER_IP</code>.</td></tr>"
    "<tr><td><code>-- Spark 3.5.1 (master) --</code></td><td>Downloads ~300 MB Spark archive and extracts it. Writes <code>spark-defaults.conf</code>.</td></tr>"
    "<tr><td><code>-- Formatting NameNode --</code></td><td>Initialises the HDFS metadata directory. Only happens once; skipped on re-runs.</td></tr>"
    "<tr><td><code>-- Starting services (master) --</code></td><td>Launches NameNode, DataNode, SecondaryNameNode, and Spark Master as background daemons.</td></tr>"
    "<tr><td><code>-- Verification --</code></td><td>Runs <code>jps</code> to list running Java processes and confirms all four are present.</td></tr>"
    "</tbody></table>"
    + tip("This takes a while the first time", "<p>Downloading Hadoop + Spark is about 1 GB total. On a fast connection expect 3-5 minutes; on a slow one, up to 20. Subsequent runs skip the download.</p>")
    + "<h4>After it finishes: check with <code>jps</code></h4>"
    "<p><code>jps</code> &mdash; the Java Virtual Machine Process Status tool &mdash; lists every running Java process. After master setup you should see exactly four:</p>"
    + cb("jps", "bash")
    + ok("Expected output &mdash; all four must appear",
        "<pre>12345 NameNode\n"
        "12346 DataNode\n"
        "12347 SecondaryNameNode\n"
        "12348 Master\n"
        "12349 Jps</pre>"
    )
    + "<p>If a process is missing, here is where to look:</p>"
    "<table>"
    "<thead><tr><th>Missing process</th><th>What to check</th></tr></thead>"
    "<tbody>"
    "<tr><td><code>NameNode</code></td><td>Check Hadoop logs in <code>$HADOOP_HOME/logs/</code>. Common cause: wrong <code>JAVA_HOME</code> in <code>hadoop-env.sh</code>.</td></tr>"
    "<tr><td><code>DataNode</code></td><td>Usually starts after NameNode. If NameNode is up but DataNode isn't, check for port 9000 conflicts: <code>lsof -i :9000</code>.</td></tr>"
    "<tr><td><code>SecondaryNameNode</code></td><td>Non-critical for this lab. Its absence won't block PageRank.</td></tr>"
    "<tr><td><code>Master</code> (Spark)</td><td>Check Spark logs in <code>$SPARK_HOME/logs/</code>.</td></tr>"
    "</tbody></table>"
)

p1_s5 = section("s1-5", "1.5", "Verify in Browser",
    "<p>Two web UIs start automatically. Open them to confirm the cluster is healthy.</p>"
    "<h4>Spark UI &mdash; <code>http://" + master_ip + ":8080</code></h4>"
    "<p>You should see the Spark Master dashboard. Look for: <strong>Status: ALIVE</strong> and at least one worker listed under &quot;Workers&quot; (the master itself counts as a worker at this stage).</p>"
    "<h4>HDFS NameNode UI &mdash; <code>http://" + master_ip + ":9870</code></h4>"
    "<p>You should see the Hadoop NameNode overview. Look for: <strong>Live Nodes: 1</strong> (or more once workers join) and <strong>Safe Mode: OFF</strong>.</p>"
    + warn("If the browser just times out", "<p>The ports are blocked by a firewall. Open them:</p>")
    + tabs(
        "# macOS -- allow incoming on these ports\nsudo /usr/libexec/ApplicationFirewall/socketfilterfw --add /usr/bin/java\n# Or turn off the firewall temporarily:\nsudo /usr/libexec/ApplicationFirewall/socketfilterfw --setglobalstate off",
        "# Linux (ufw)\nsudo ufw allow 8080\nsudo ufw allow 9870\nsudo ufw allow 9000\nsudo ufw allow 7077\nsudo ufw allow 5000",
        "# Windows PowerShell (run as Administrator)\nnetsh advfirewall firewall add rule name=\"Spark\" dir=in action=allow protocol=TCP localport=8080\nnetsh advfirewall firewall add rule name=\"HDFS\" dir=in action=allow protocol=TCP localport=9870\nnetsh advfirewall firewall add rule name=\"SparkMaster\" dir=in action=allow protocol=TCP localport=7077",
    )
)

p1_s6 = section("s1-6", "1.6", "Load the Dataset",
    "<p>The dataset is the Stanford Web-Google graph &mdash; a snapshot of 875,713 web pages and 5,105,039 hyperlinks between them, "
    "collected by Google in 2002. HDFS (the Hadoop Distributed File System) stores data across all nodes so Spark can read it in parallel.</p>"
    "<h4>Step 1 &mdash; Download</h4>"
    + cb("python3 src/download_dataset.py", "bash")
    + ok("Expected output",
        "<pre>Downloading from https://snap.stanford.edu/data/web-Google.txt.gz ...\n"
        "  [####################] 100%\n"
        "Extracting...\n\n"
        "[ok] Ready: data/web-Google.txt\n"
        "  Nodes: 875,713\n"
        "  Edges: 5,105,039\n\n"
        "Next: hdfs dfs -put data/web-Google.txt /pagerank/input/</pre>"
    )
    + "<h4>Step 2 &mdash; Push to HDFS</h4>"
    "<p><code>hdfs dfs -put</code> copies a local file into the distributed filesystem so all workers can access it.</p>"
    + cb("hdfs dfs -put data/web-Google.txt /pagerank/input/", "bash")
    + ok("Expected output",
        "<p>No output means success. Verify the file landed:</p>"
        "<pre>hdfs dfs -ls /pagerank/input/\n\n"
        "-rw-r--r--   2 user supergroup  804298888 2024-05-09 /pagerank/input/web-Google.txt</pre>"
    )
    + tip("Already in HDFS?", "<p>If you re-run, use <code>hdfs dfs -put -f</code> (force overwrite) to replace an existing file.</p>")
)

p1_s7 = section("s1-7", "1.7", "Run PageRank",
    "<p>This submits the PageRank job to Spark. <code>spark-submit</code> packages your Python script and sends it to the Spark Master, which distributes the computation across all connected workers.</p>"
    + cb(
        "spark-submit \\\n"
        "  --master spark://" + master_ip + ":7077 \\\n"
        "  --executor-memory 2g \\\n"
        "  --driver-memory 1g \\\n"
        "  src/pagerank.py 10",
        "bash"
    )
    + "<p>The number <code>10</code> is the iteration count. During the run you will see lines like:</p>"
    + ok("Iteration output",
        "<pre>  Iteration  1/10  12.3s\n"
        "  Iteration  2/10  11.8s\n"
        "  Iteration  3/10  11.5s\n"
        "  ...\n"
        "  Iteration 10/10  11.2s\n\n"
        "Collecting results...\n\n"
        "=======================================================\n"
        "  TOP 5 MOST INFLUENTIAL NODES\n"
        "=======================================================\n"
        "  #1  node      41909  ->  445.71778597\n"
        "  #2  node     597621  ->  406.62836675\n"
        "  #3  node     504140  ->  399.08930875\n"
        "  #4  node     384666  ->  392.82584373\n"
        "  #5  node     537039  ->  383.90912550\n"
        "=======================================================\n\n"
        "[ok] Done in 118.4s</pre>"
    )
    + "<p>Each iteration line shows the wall-clock time for one pass over the graph. Times should be roughly stable; a sudden spike usually means a worker disconnected.</p>"
    "<h4>Where results are saved</h4>"
    "<table>"
    "<thead><tr><th>File</th><th>Contents</th></tr></thead>"
    "<tbody>"
    "<tr><td><code>data/top5.json</code></td><td>Top 5 nodes &mdash; this is what the API serves.</td></tr>"
    "<tr><td><code>data/results.json</code></td><td>Top 1000 nodes with scores, for <code>/node/&lt;id&gt;</code> and <code>/top/&lt;n&gt;</code> queries.</td></tr>"
    "<tr><td><code>data/graph.json</code></td><td>Full adjacency list &mdash; every node and its outgoing neighbors. Used by <code>/neighbors</code> and <code>/influencedby</code>.</td></tr>"
    "<tr><td><code>data/meta.json</code></td><td>Job metadata &mdash; dataset name, node/edge counts, iterations, damping factor, top node, completion timestamp. Used by <code>/stats</code>.</td></tr>"
    "<tr><td><code>data/pagerank_output/part-00000</code></td><td>All nodes, tab-separated: <code>nodeId\\tscore</code>.</td></tr>"
    "</tbody></table>"
)

p1_s8 = section("s1-8", "1.8", "Start the API",
    "<p>The REST API is a small Flask server that reads <code>data/top5.json</code> and serves it to other groups over HTTP.</p>"
    "<h4>Verify locally first</h4>"
    + cb("python3 src/api.py", "bash")
    + ok("Expected startup output",
        "<pre>==================================================\n"
        "  Group 03 - PageRank Portability API\n"
        "  http://" + master_ip + ":5000\n\n"
        "  GET  /top5              -> top 5 influencers\n"
        "  GET  /top/&lt;n&gt;          -> top N ranked nodes\n"
        "  GET  /node/&lt;id&gt;         -> score for node id\n"
        "  GET  /neighbors/&lt;id&gt;    -> outgoing edges\n"
        "  GET  /influencedby/&lt;id&gt; -> incoming edges\n"
        "  GET  /stats             -> job metadata + service info\n"
        "  POST /rerun             -> trigger background rerun\n"
        "  GET  /rerun/status      -> rerun job status\n"
        "  GET  /health            -> status check\n\n"
        "  [ok] Results loaded -- top node: " + top_node + " (" + top_score + ")\n"
        "==================================================</pre>"
    )
    + "<p>In a second terminal, confirm it responds:</p>"
    + cb("curl http://localhost:5000/health", "bash")
    + "<h4>Run it in the background (so you can close the terminal)</h4>"
    + tabs(
        "nohup python3 src/api.py > /tmp/api.log 2>&1 &\necho \"API PID: $!\"\n# To stop it later:\n# kill $(lsof -ti :5000)",
        "nohup python3 src/api.py > /tmp/api.log 2>&1 &\necho \"API PID: $!\"\n# To stop it later:\n# kill $(lsof -ti :5000)",
        "# PowerShell -- start as a background job\nStart-Job -ScriptBlock { python3 src/api.py } | Out-Null\nWrite-Host 'API started in background'\n# To stop: Get-Job | Stop-Job",
    )
    + "<h4>Three ways to verify it works</h4>"
    + cb(
        "# Option 1 -- curl\n"
        "curl http://localhost:5000/health\n\n"
        "# Option 2 -- Python (works on all three OS)\n"
        "python3 -c \"import urllib.request, json; print(json.loads(urllib.request.urlopen('http://localhost:5000/health').read()))\"\n\n"
        "# Option 3 -- Browser\n"
        "# Open: http://localhost:5000/health",
        "bash"
    )
    + tip("macOS port 5000 conflict", "<p>macOS Monterey+ reserves port 5000 for AirPlay Receiver. If <code>curl</code> returns <em>connection refused</em>, go to <strong>System Settings &rarr; AirDrop &amp; Handoff</strong> and turn off AirPlay Receiver. Then restart the API.</p>")
)

# ==============================================================================
# PART 2 CONTENT
# ==============================================================================

p2_s1 = section("s2-1", "2.1", "Before You Start",
    "<p>The master node must be fully running before you set up any worker. Specifically:</p>"
    "<ul>"
    "  <li>Section 1.4 must be complete &mdash; <code>jps</code> on the master shows all four processes.</li>"
    "  <li>You need the master's LAN IP address from Section 1.2.</li>"
    "  <li>Both machines must be on the same Wi-Fi or wired LAN.</li>"
    "</ul>"
    + cb(
        "# Quick connectivity check from the worker machine:\n"
        "ping -c 3 " + master_ip + "\n"
        "# All 3 packets should receive a reply.",
        "bash"
    )
    + warn("Different Wi-Fi networks", "<p>University campuses often have network isolation between clients on the same SSID. If ping fails even though you're on the same network, use a personal hotspot or a wired switch shared between the machines.</p>")
)

p2_s2 = section("s2-2", "2.2", "Clone and Configure",
    "<h4>Clone the repository on the worker machine</h4>"
    + cb("git clone https://github.com/munimx/pagerank-cluster\ncd pagerank-cluster", "bash")
    + "<h4>Set <code>MASTER_IP</code> in <code>setup/config.py</code></h4>"
    "<p>Open the file and change the one line:</p>"
    + cb('MASTER_IP = "192.168.1.42"   # the MASTER\'s LAN IP, NOT your own', "python")
    + warn("Common mistake &mdash; setting MASTER_IP to your own IP on a worker machine",
        "<p>On the <strong>worker</strong>, <code>MASTER_IP</code> must be the IP of the <strong>master laptop</strong>, not the worker's own IP. "
        "If you set it to your own IP, the worker will try to connect to itself as a master &mdash; and fail silently. "
        "Double-check before running setup.</p>"
    )
)

p2_s3 = section("s2-3", "2.3", "Run Worker Setup",
    cb("python3 setup/setup_node.py --role worker", "bash")
    + "<p>This installs Java, Python dependencies, Hadoop, and Spark &mdash; same as the master, but starts only the DataNode and Spark Worker daemons (not the NameNode or Spark Master).</p>"
    "<h4>After it finishes: check with <code>jps</code></h4>"
    + cb("jps", "bash")
    + ok("Expected output on the worker &mdash; exactly these two",
        "<pre>23456 DataNode\n"
        "23457 Worker\n"
        "23458 Jps</pre>"
        "<p>You should <strong>not</strong> see <code>NameNode</code> or <code>Master</code> on a worker &mdash; those only run on the master machine.</p>"
    )
)

p2_s4 = section("s2-4", "2.4", "Register with Master",
    "<p>The master needs to know this worker exists. This is a two-step handshake: the worker reports its IP, then the master adds it to the cluster roster.</p>"
    "<h4>Step 1 &mdash; Find your own IP (on the worker machine)</h4>"
    + tabs(
        "ipconfig getifaddr en0",
        "hostname -I | awk '{print $1}'",
        "(Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.IPAddress -like '192.168.*' }).IPAddress",
    )
    + "<h4>Step 2 &mdash; Send your IP to the master operator</h4>"
    "<p>Tell the person running the master laptop your IP (e.g., via Slack, Discord, or just say it out loud). They run this on the master:</p>"
    + cb("# On the MASTER machine -- replace with the worker's actual IP\npython3 setup/register_worker.py 192.168.1.55", "bash")
    + "<h4>Step 3 &mdash; Verify from the master</h4>"
    + cb("hdfs dfsadmin -report | grep 'Live datanodes'", "bash")
    + ok("Expected output",
        "<p><code>Live datanodes (2):</code> &mdash; the count increases by 1 each time a worker is registered. "
        "If you have 1 worker plus the master's own DataNode, you'll see 2.</p>"
    )
)

p2_s5 = section("s2-5", "2.5", "Most Common Failures",
    "<h4>Failure 1 &mdash; <code>MASTER_IP</code> mismatch</h4>"
    "<p>The worker starts but never appears in the Spark UI or HDFS report.</p>"
    + ok("What the error looks like in Spark Worker logs",
        "<pre>ERROR Worker: All masters are unresponsive! Giving up.\n"
        "ERROR Worker: Connection to spark://192.168.1.99:7077 failed</pre>"
    )
    + "<p><strong>Fix:</strong> Open <code>setup/config.py</code> on the <em>worker</em> machine and correct <code>MASTER_IP</code> to the master's actual LAN IP. Then re-run worker setup.</p>"
    "<h4>Failure 2 &mdash; Worker can't reach master (firewall)</h4>"
    "<p>Ping succeeds but Spark/HDFS connections time out.</p>"
    + tabs(
        "# macOS -- allow Java through the firewall\nsudo /usr/libexec/ApplicationFirewall/socketfilterfw --add /usr/bin/java\n# Or disable the firewall temporarily:\nsudo /usr/libexec/ApplicationFirewall/socketfilterfw --setglobalstate off",
        "sudo ufw allow from 192.168.1.0/24\n# Or open specific ports:\nsudo ufw allow 7077\nsudo ufw allow 9000\nsudo ufw allow 9866",
        "# Run as Administrator\nnetsh advfirewall firewall add rule name=\"Hadoop-Spark\" dir=in action=allow protocol=TCP localport=7077,9000,9866,9870",
    )
)

# ==============================================================================
# PART 3 CONTENT
# ==============================================================================

p3_intro = (
    "<p>The portability test checks that your group's API can be queried by a <em>different</em> group's machine &mdash; "
    "confirming the result is not just local but genuinely accessible over the LAN. You are querying the Group 03 master "
    "node for the top-5 most influential pages in the Stanford Web-Google graph, as computed by our distributed PageRank job. "
    "The three endpoints below must all return valid JSON.</p>"
)

p3_s1 = section("s3-1", "3.1", "Check the Service Is Up",
    "<p>Before querying results, confirm the API process is alive.</p>"
    "<h4>Three ways to call <code>GET /health</code></h4>"
    + cb(
        "# curl\n"
        "curl http://" + master_ip + ":5000/health\n\n"
        "# Python\n"
        "python3 -c \"import urllib.request, json; print(json.dumps(json.loads(urllib.request.urlopen('http://" + master_ip + ":5000/health').read()), indent=2))\"\n\n"
        "# Browser\n"
        "# http://" + master_ip + ":5000/health",
        "bash"
    )
    + ok("Healthy response",
        '<pre>{\n'
        '  "dataset": "Stanford Web-Google",\n'
        '  "framework": "Apache Spark",\n'
        '  "group": "03",\n'
        '  "results_ready": true,\n'
        '  "status": "ok",\n'
        '  "task": "Network Graph PageRank"\n'
        '}</pre>'
    )
    + warn("Failed / unexpected response",
        "<p>If the connection is refused: the API process isn't running. Contact the Group 03 master operator to restart it (<code>python3 src/api.py &amp;</code>).</p>"
        "<p>If you get a timeout: check network connectivity with <code>ping</code> first, then check firewall rules (Section 2.5).</p>"
    )
)

p3_s2 = section("s3-2", "3.2", "Query the Top 5 Results",
    "<p><code>GET /top5</code> returns the five highest-ranked nodes in the Web-Google graph.</p>"
    + cb(
        "# curl\n"
        "curl http://" + master_ip + ":5000/top5\n\n"
        "# Python urllib (no extra libraries needed)\n"
        "python3 -c \"\n"
        "import urllib.request, json\n"
        "data = json.loads(urllib.request.urlopen('http://" + master_ip + ":5000/top5').read())\n"
        "for n in data:\n"
        "    print(n['rank'], n['nodeId'], n['pagerank'])\n"
        "\"\n\n"
        "# Browser\n"
        "# http://" + master_ip + ":5000/top5",
        "bash"
    )
    + ok("Expected JSON response", "<pre>" + esc(top5_json_str) + "</pre>")
    + tip("Scores may differ slightly",
        "<p>PageRank scores depend on the number of iterations and the damping factor. "
        "Our run used 10 iterations and damping 0.85. Node IDs will match; the exact floating-point values "
        "may vary by &plusmn;0.001 if you re-run with different settings.</p>"
    )
)

p3_s3 = section("s3-3", "3.3", "Query a Specific Node",
    "<p><code>GET /node/&lt;id&gt;</code> returns the score for one node. Use the top-ranked node's ID as your test case.</p>"
    + cb(
        "# curl -- query the top node\n"
        "curl http://" + master_ip + ":5000/node/" + top_node + "\n\n"
        "# Python\n"
        "python3 -c \"\n"
        "import urllib.request, json\n"
        "data = json.loads(urllib.request.urlopen('http://" + master_ip + ":5000/node/" + top_node + "').read())\n"
        "print(json.dumps(data, indent=2))\n"
        "\"",
        "bash"
    )
    + ok("Expected response",
        '<pre>{\n'
        '  "nodeId": "' + top_node + '",\n'
        '  "pagerank": ' + top_score + '\n'
        '}</pre>'
    )
)

p3_s4 = section("s3-4", "3.4", "Query a Specific Node",
    "<p><code>GET /node/&lt;id&gt;</code> returns the score for one node. Use the top-ranked node's ID as your test case.</p>"
    + cb(
        "# curl -- query the top node\n"
        "curl http://" + master_ip + ":5000/node/" + top_node + "\n\n"
        "# Python\n"
        "python3 -c \"\n"
        "import urllib.request, json\n"
        "data = json.loads(urllib.request.urlopen('http://" + master_ip + ":5000/node/" + top_node + "').read())\n"
        "print(json.dumps(data, indent=2))\n"
        "\"",
        "bash"
    )
    + ok("Expected response",
        '<pre>{\n'
        '  "nodeId": "' + top_node + '",\n'
        '  "pagerank": ' + top_score + '\n'
        '}</pre>'
    )
)

p3_s5 = section("s3-5", "3.5", "Top N Nodes",
    "<p><code>GET /top/&lt;n&gt;</code> returns the top <em>n</em> ranked nodes (capped at 1000, the size of the stored result set).</p>"
    + cb(
        "# Get top 10 nodes\n"
        "curl http://" + master_ip + ":5000/top/10\n\n"
        "# Get top 50 nodes\n"
        "curl http://" + master_ip + ":5000/top/50",
        "bash"
    )
    + ok("Response format",
        '<pre>{\n'
        '  "requested": 10,\n'
        '  "returned": 10,\n'
        '  "nodes": [\n'
        '    {"nodeId": "41909", "pagerank": 445.71778597},\n'
        '    {"nodeId": "597621", "pagerank": 406.62836675},\n'
        '    ...\n'
        '  ]\n'
        '}</pre>'
    )
    + "<h4>Edge cases</h4>"
    "<ul>"
    "<li><code>n &lt; 1</code> &rarr; returns <code>400</code> with error message.</li>"
    "<li><code>n &gt; 1000</code> &rarr; returns all 1000 available nodes with a <code>note</code> field explaining the cap.</li>"
    "</ul>"
)

p3_s6 = section("s3-6", "3.6", "Outgoing Edges (Neighbors)",
    "<p><code>GET /neighbors/&lt;node_id&gt;</code> returns every node that the given node links <em>to</em> (outgoing edges, i.e. the node's adjacency list).</p>"
    + cb(
        "# Get all outgoing neighbors of the top-ranked node\n"
        "curl http://" + master_ip + ":5000/neighbors/" + top_node + "\n\n"
        "# Python\n"
        "python3 -c \"\n"
        "import urllib.request, json\n"
        "data = json.loads(urllib.request.urlopen('http://" + master_ip + ":5000/neighbors/" + top_node + "').read())\n"
        "print(json.dumps(data, indent=2))\n"
        "\"",
        "bash"
    )
    + ok("Response format",
        '<pre>{\n'
        '  "nodeId": "' + top_node + '",\n'
        '  "direction": "outgoing",\n'
        '  "count": 42,\n'
        '  "neighbors": ["123", "456", "789", ...]\n'
        '}</pre>'
    )
    + "<h4>Sink nodes</h4>"
    "<p>Nodes with no outgoing edges (sink nodes) will return <code>404</code> with the message: "
    "<em>This may be a sink node (has no outgoing edges — it receives links but doesn't link to anything).</em> "
    "This is expected behaviour &mdash; sink nodes exist in the graph but have no entries in the adjacency list.</p>"
)

p3_s7 = section("s3-7", "3.7", "Incoming Edges (Influencers)",
    "<p><code>GET /influencedby/&lt;node_id&gt;</code> returns every node that links <em>to</em> the given node (incoming edges). "
    "This is computed on first request by building a reverse-index from <code>data/graph.json</code>, "
    "then cached in memory for all subsequent calls &mdash; it does not rebuild on every request.</p>"
    + cb(
        "# Get all nodes that link to the top-ranked node\n"
        "curl http://" + master_ip + ":5000/influencedby/" + top_node + "\n\n"
        "# Python\n"
        "python3 -c \"\n"
        "import urllib.request, json\n"
        "data = json.loads(urllib.request.urlopen('http://" + master_ip + ":5000/influencedby/" + top_node + "').read())\n"
        "print(f\\\"Node {data['nodeId']} is influenced by {data['count']} nodes\\\")\n"
        "\"",
        "bash"
    )
    + ok("Response format",
        '<pre>{\n'
        '  "nodeId": "' + top_node + '",\n'
        '  "direction": "incoming",\n'
        '  "count": 18,\n'
        '  "sources": ["789", "101", "202", ...]\n'
        '}</pre>'
    )
)

p3_s8 = section("s3-8", "3.8", "Job Statistics",
    "<p><code>GET /stats</code> returns the job metadata recorded when <code>pagerank.py</code> finished, plus live service information.</p>"
    + cb(
        "curl http://" + master_ip + ":5000/stats\n\n"
        "# Python\n"
        "python3 -c \"\n"
        "import urllib.request, json\n"
        "print(json.dumps(json.loads(urllib.request.urlopen('http://" + master_ip + ":5000/stats').read()), indent=2))\n"
        "\"",
        "bash"
    )
    + ok("Response format",
        '<pre>{\n'
        '  "dataset": "web-Google.txt",\n'
        '  "total_nodes": 875713,\n'
        '  "total_edges": 5105039,\n'
        '  "iterations": 10,\n'
        '  "damping_factor": 0.85,\n'
        '  "top_node": "' + top_node + '",\n'
        '  "completed_at": "2026-05-10T12:34:56+00:00",\n'
        '  "api_status": "ok",\n'
        '  "endpoints": ["/top5", "/top/<n>", "/node/<id>", "/neighbors/<id>", "/influencedby/<id>", "/stats", "/rerun", "/health"]\n'
        '}</pre>'
    )
)

p3_s9 = section("s3-9", "3.9", "Background Rerun",
    "<p><code>POST /rerun</code> triggers a PageRank rerun in the background. "
    "It accepts optional parameters to change the iteration count, damping factor, or swap to an entirely different dataset from SNAP.</p>"
    + cb(
        "# Rerun with more iterations\n"
        "curl -X POST http://" + master_ip + ":5000/rerun \\\n"
        "  -H 'Content-Type: application/json' \\\n"
        "  -d '{\"iterations\": 15}'\n\n"
        "# Rerun with different damping factor\n"
        "curl -X POST http://" + master_ip + ":5000/rerun \\\n"
        "  -H 'Content-Type: application/json' \\\n"
        "  -d '{\"damping_factor\": 0.90}'\n\n"
        "# Swap dataset entirely — Twitter graph from SNAP\n"
        "curl -X POST http://" + master_ip + ":5000/rerun \\\n"
        "  -H 'Content-Type: application/json' \\\n"
        "  -d '{\"dataset_url\": \"https://snap.stanford.edu/data/twitter_combined.txt.gz\"}'\n\n"
        "# Combine all parameters\n"
        "curl -X POST http://" + master_ip + ":5000/rerun \\\n"
        "  -H 'Content-Type: application/json' \\\n"
        "  -d '{\"iterations\": 20, \"damping_factor\": 0.88, \"dataset_url\": \"https://snap.stanford.edu/data/web-Google.txt.gz\"}'",
        "bash"
    )
    + ok("Immediate response (202 Accepted)",
        '<pre>{\n'
        '  "job_id": "rerun_1746861234",\n'
        '  "status": "queued",\n'
        '  "params": {"iterations": 15}\n'
        '}</pre>'
    )
    + "<h4>Check job status</h4>"
    + cb(
        "curl http://" + master_ip + ":5000/rerun/status",
        "bash"
    )
    + ok("Status responses",
        '<pre>// idle (no rerun ever triggered)\n'
        '{"status": "idle"}\n\n'
        '// running\n'
        '{"status": "running", "job_id": "rerun_1746861234", "started_at": "2026-05-10T12:00:00+00:00", ...}\n\n'
        '// completed\n'
        '{"status": "completed", "job_id": "rerun_1746861234", "completed_at": "2026-05-10T12:02:45+00:00", ...}\n\n'
        '// failed\n'
        '{"status": "failed", "job_id": "rerun_1746861234", "error": "..."}</pre>'
    )
    + warn("Dataset swap requires a SNAP URL",
        "<p>When <code>dataset_url</code> is provided, the API downloads the file, places it in HDFS, updates the metadata, "
        "then runs <code>pagerank.py</code>. The URL must point to a gzipped SNAP graph file (e.g. from "
        "<code>https://snap.stanford.edu/data/</code>). The file is downloaded locally, extracted, then pushed to HDFS "
        "so it is available to all cluster nodes.</p>"
    )
    + tip("The API stays responsive during a rerun",
        "<p>The rerun happens in a background thread. The API continues to serve requests using the <em>previous</em> "
        "results until the new job completes. When the job finishes, the API updates all result files and future queries "
        "return the new results. The reverse-index cache is also invalidated so <code>/influencedby</code> reflects the new graph.</p>"
    )
)

p3_s10 = section("s3-10", "3.10", "If Something Fails",
    "<h4>API unreachable (connection refused / timeout)</h4>"
    "<p>Step 1: confirm basic network connectivity first.</p>"
    + cb("ping -c 4 " + master_ip, "bash")
    + "<p>If ping fails, you are on different networks. If ping succeeds but the API is still unreachable, "
    "the firewall is blocking port 5000. Apply the firewall rules from Section 2.5 on the <strong>master</strong> machine.</p>"
    "<h4>503 response &mdash; results not ready</h4>"
    + ok("503 response body",
        '<pre>{"error": "Results not ready. Run src/pagerank.py first."}</pre>'
        "<p>The PageRank job has not finished yet (or has not been run at all). Contact the Group 03 master operator. "
        "Do not mark the portability test as failed immediately &mdash; the job takes approximately 2 minutes to complete.</p>"
    )
    + "<h4>404 on a node ID</h4>"
    + ok("404 response body",
        "<pre>" + esc('{"error": "Node \'999999\' not in top-1000 results."}') + "</pre>"
        "<p>The API only stores the top 1000 nodes by PageRank score. A 404 for a node ID that is not in the top 1000 "
        "is expected and correct behaviour &mdash; it does not indicate a bug.</p>"
    )
)

# ==============================================================================
# CSS + JS (no f-strings needed — no interpolation)
# ==============================================================================

CSS = """
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

:root {
  --ink:        #0f1117;
  --ink-2:      #3a3d4a;
  --ink-3:      #717484;
  --canvas:     #fafafa;
  --surface:    #f3f4f7;
  --surface-2:  #eaecf2;
  --border:     #dde0eb;
  --border-2:   #c8ccdb;
  --accent:     #1a56db;
  --accent-dim: #dbeafe;
  --warn:       #92400e;
  --warn-bg:    #fffbeb;
  --warn-border:#fbbf24;
  --ok:         #065f46;
  --ok-bg:      #ecfdf5;
  --ok-border:  #34d399;
  --tip:        #1e40af;
  --tip-bg:     #eff6ff;
  --tip-border: #93c5fd;
  --code-bg:    #111827;
  --code-text:  #e5e7eb;
  --code-border:#374151;
  --sidebar-w:  260px;
  --content-w:  780px;
  --mono:       'IBM Plex Mono', 'Fira Code', monospace;
  --sans:       'Sora', -apple-system, sans-serif;
  --r:          6px;
}

html { scroll-behavior: smooth; }
body {
  font-family: var(--sans);
  background: var(--canvas);
  color: var(--ink);
  line-height: 1.75;
  font-size: 15px;
  font-weight: 300;
}

.layout { display: flex; min-height: 100vh; }

.sidebar {
  width: var(--sidebar-w);
  flex-shrink: 0;
  position: sticky;
  top: 0;
  height: 100vh;
  overflow-y: auto;
  border-right: 1px solid var(--border);
  background: var(--canvas);
  display: flex;
  flex-direction: column;
  z-index: 100;
}

.main { flex: 1; min-width: 0; padding: 0 clamp(20px, 5vw, 80px) 100px; }
.content { max-width: var(--content-w); margin: 0 auto; }

.sidebar-header { padding: 24px 20px 16px; border-bottom: 1px solid var(--border); }
.sidebar-logo { font-size: 11px; font-weight: 700; letter-spacing: 2px; text-transform: uppercase; color: var(--ink-3); margin-bottom: 4px; }
.sidebar-title { font-size: 13px; font-weight: 700; color: var(--ink); line-height: 1.3; }

.toc { padding: 16px 0 24px; flex: 1; }
.toc-part { padding: 8px 20px 4px; font-size: 10px; font-weight: 700; letter-spacing: 2px; text-transform: uppercase; color: var(--ink-3); margin-top: 8px; }
.toc-link { display: block; padding: 5px 20px 5px 28px; font-size: 12.5px; color: var(--ink-2); text-decoration: none; border-left: 2px solid transparent; transition: all 0.15s; line-height: 1.4; }
.toc-link:hover { color: var(--accent); background: var(--accent-dim); }
.toc-link.active { color: var(--accent); border-left-color: var(--accent); background: var(--accent-dim); font-weight: 600; }

.hamburger { display: none; position: fixed; top: 16px; left: 16px; z-index: 200; width: 40px; height: 40px; background: var(--ink); border: none; border-radius: var(--r); cursor: pointer; flex-direction: column; align-items: center; justify-content: center; gap: 5px; transition: background 0.2s; }
.hamburger span { display: block; width: 20px; height: 2px; background: #fff; border-radius: 2px; transition: all 0.25s; }
.hamburger.open span:nth-child(1) { transform: translateY(7px) rotate(45deg); }
.hamburger.open span:nth-child(2) { opacity: 0; }
.hamburger.open span:nth-child(3) { transform: translateY(-7px) rotate(-45deg); }

.cover { background: var(--ink); color: #fff; padding: 72px 0 64px; }
.cover-inner { max-width: var(--content-w); margin: 0 auto; }
.cover-badge { display: inline-block; font-family: var(--mono); font-size: 11px; font-weight: 600; letter-spacing: 1.5px; background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.2); border-radius: 4px; padding: 3px 10px; margin-bottom: 24px; color: rgba(255,255,255,0.7); }
.cover h1 { font-size: clamp(28px, 5vw, 46px); font-weight: 800; line-height: 1.1; letter-spacing: -1.5px; margin-bottom: 12px; }
.cover-sub { font-size: 15px; color: rgba(255,255,255,0.55); margin-bottom: 36px; font-weight: 300; }
.cover-chips { display: flex; flex-wrap: wrap; gap: 8px; }
.chip { font-family: var(--mono); font-size: 11px; background: rgba(255,255,255,0.07); border: 1px solid rgba(255,255,255,0.15); padding: 4px 12px; border-radius: 20px; color: rgba(255,255,255,0.6); }

.part-divider { margin: 72px 0 0; padding: 36px 0 32px; border-top: 2px solid var(--border-2); position: relative; }
.part-divider::before { content: ''; position: absolute; top: -2px; left: 0; width: 60px; height: 2px; background: var(--accent); }
.part-label { font-family: var(--mono); font-size: 11px; letter-spacing: 2px; text-transform: uppercase; color: var(--accent); margin-bottom: 6px; }
.part-title { font-size: clamp(22px, 4vw, 32px); font-weight: 800; letter-spacing: -0.5px; color: var(--ink); line-height: 1.15; }

section { margin-top: 52px; padding-top: 8px; }
section h3 { font-size: 18px; font-weight: 700; color: var(--ink); margin-bottom: 16px; display: flex; align-items: baseline; gap: 12px; }
.sec-num { font-family: var(--mono); font-size: 12px; color: var(--ink-3); font-weight: 600; flex-shrink: 0; }
h4 { font-size: 13.5px; font-weight: 700; color: var(--ink); margin: 24px 0 8px; }
p { margin-bottom: 12px; color: var(--ink-2); }
ul, ol { padding-left: 20px; margin-bottom: 14px; color: var(--ink-2); }
li { margin-bottom: 6px; }
code { font-family: var(--mono); font-size: 12.5px; background: var(--surface-2); color: #b91c1c; padding: 1px 5px; border-radius: 3px; }

.code-wrap { position: relative; margin: 12px 0 20px; }
.code-wrap pre { background: var(--code-bg); border: 1px solid var(--code-border); border-radius: var(--r); padding: 18px 20px; overflow-x: auto; font-family: var(--mono); font-size: 12.5px; line-height: 1.65; color: var(--code-text); tab-size: 2; }
.code-wrap pre code { background: none; color: inherit; padding: 0; font-size: inherit; border-radius: 0; }
.copy-btn { position: absolute; top: 10px; right: 10px; font-family: var(--mono); font-size: 11px; font-weight: 600; color: #9ca3af; background: #1f2937; border: 1px solid #374151; border-radius: 4px; padding: 3px 10px; cursor: pointer; transition: all 0.15s; z-index: 2; }
.copy-btn:hover { background: #374151; color: #f9fafb; border-color: #4b5563; }
.copy-btn.copied { color: #34d399; border-color: #34d399; }

.os-tabs { margin: 12px 0 20px; border: 1px solid var(--border); border-radius: var(--r); overflow: hidden; }
.os-tab-bar { display: flex; background: var(--surface); border-bottom: 1px solid var(--border); }
.os-tab { font-family: var(--mono); font-size: 11.5px; font-weight: 600; padding: 8px 18px; background: none; border: none; border-right: 1px solid var(--border); color: var(--ink-3); cursor: pointer; transition: all 0.15s; }
.os-tab:last-child { border-right: none; }
.os-tab:hover { background: var(--surface-2); color: var(--ink); }
.os-tab.active { background: var(--canvas); color: var(--accent); border-bottom: 2px solid var(--accent); margin-bottom: -1px; }
.os-pane { display: none; }
.os-pane.active { display: block; }
.os-pane .code-wrap { margin: 0; }
.os-pane .code-wrap pre { border: none; border-radius: 0; }

.callout { display: flex; gap: 12px; padding: 14px 16px; border-radius: var(--r); margin: 16px 0; border: 1px solid; }
.callout-warn { background: var(--warn-bg); border-color: var(--warn-border); color: var(--warn); }
.callout-ok { background: var(--ok-bg); border-color: var(--ok-border); color: var(--ok); }
.callout-tip { background: var(--tip-bg); border-color: var(--tip-border); color: var(--tip); }
.callout-icon { font-size: 15px; flex-shrink: 0; margin-top: 1px; }
.callout strong { display: block; font-size: 13px; font-weight: 700; margin-bottom: 4px; }
.callout p { margin: 0; font-size: 13.5px; line-height: 1.6; color: inherit; }
.callout pre { background: rgba(0,0,0,0.06); border: none; border-radius: 4px; padding: 10px 12px; margin-top: 8px; font-size: 12px; line-height: 1.5; color: inherit; overflow-x: auto; font-family: var(--mono); }
.callout code { background: rgba(0,0,0,0.08); color: inherit; padding: 1px 4px; }

table { width: 100%; border-collapse: collapse; margin: 16px 0 24px; font-size: 13.5px; }
thead tr { background: var(--ink); color: #fff; }
th { text-align: left; padding: 10px 14px; font-weight: 600; font-size: 12px; white-space: nowrap; }
td { padding: 9px 14px; border-bottom: 1px solid var(--border); vertical-align: top; color: var(--ink-2); line-height: 1.55; }
tr:last-child td { border-bottom: none; }
tbody tr:hover td { background: var(--surface); }
.results-table .rank { font-family: var(--mono); font-weight: 600; color: var(--ink); }
.results-table .score { font-family: var(--mono); color: var(--accent); }

.muted { color: var(--ink-3); font-style: italic; }

footer { margin-top: 80px; padding: 32px 0; border-top: 1px solid var(--border); font-size: 12px; color: var(--ink-3); font-family: var(--mono); text-align: center; }

@media print {
  .sidebar, .hamburger { display: none !important; }
  .layout { display: block; }
  .main { padding: 0; }
  .content { max-width: 100%; }
  .cover { background: #000 !important; -webkit-print-color-adjust: exact; print-color-adjust: exact; }
  .code-wrap pre { background: #111 !important; color: #e5e7eb !important; -webkit-print-color-adjust: exact; print-color-adjust: exact; white-space: pre-wrap; word-break: break-word; }
  .copy-btn { display: none; }
  .os-tabs .os-pane { display: block !important; }
  .os-pane .code-wrap pre { border-top: 1px solid #374151; }
  .os-tab-bar { display: none; }
  section { page-break-inside: avoid; }
  .part-divider { page-break-before: always; }
}

@media (max-width: 900px) {
  .hamburger { display: flex; }
  .sidebar { position: fixed; left: -100%; top: 0; height: 100vh; transition: left 0.25s ease; box-shadow: 4px 0 30px rgba(0,0,0,0.12); }
  .sidebar.open { left: 0; }
  .main { padding-top: 60px; }
}
"""

JS = """
const OS_KEY = 'preferred-os';

function activateOS(os) {
  document.querySelectorAll('.os-tab').forEach(t => t.classList.toggle('active', t.dataset.os === os));
  document.querySelectorAll('.os-pane').forEach(p => p.classList.toggle('active', p.dataset.os === os));
  try { localStorage.setItem(OS_KEY, os); } catch(e) {}
}

function initTabs() {
  const saved = (() => { try { return localStorage.getItem(OS_KEY); } catch(e) { return null; } })();
  activateOS(saved || 'macos');
  document.querySelectorAll('.os-tab').forEach(tab => tab.addEventListener('click', () => activateOS(tab.dataset.os)));
}

function initCopyButtons() {
  document.querySelectorAll('.copy-btn').forEach(btn => {
    btn.addEventListener('click', async () => {
      const code = btn.nextElementSibling.querySelector('code');
      const text = code ? code.innerText : '';
      try {
        await navigator.clipboard.writeText(text);
      } catch(err) {
        const ta = document.createElement('textarea');
        ta.value = text; ta.style.position = 'fixed'; ta.style.opacity = '0';
        document.body.appendChild(ta); ta.select(); document.execCommand('copy');
        document.body.removeChild(ta);
      }
      btn.textContent = '✓ Copied';
      btn.classList.add('copied');
      setTimeout(() => { btn.textContent = 'Copy'; btn.classList.remove('copied'); }, 2000);
    });
  });
}

function initScrollSpy() {
  const links = Array.from(document.querySelectorAll('.toc-link'));
  const targets = links.map(l => document.querySelector(l.getAttribute('href'))).filter(Boolean);
  const observer = new IntersectionObserver(entries => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const id = entry.target.id;
        links.forEach(l => l.classList.toggle('active', l.getAttribute('href') === '#' + id));
      }
    });
  }, { rootMargin: '-10% 0px -80% 0px', threshold: 0 });
  targets.forEach(t => observer.observe(t));
}

function initHamburger() {
  const btn = document.getElementById('hamburger');
  const sidebar = document.getElementById('sidebar');
  btn.addEventListener('click', () => {
    const open = sidebar.classList.toggle('open');
    btn.classList.toggle('open', open);
  });
  sidebar.querySelectorAll('.toc-link').forEach(l => l.addEventListener('click', () => {
    sidebar.classList.remove('open'); btn.classList.remove('open');
  }));
  document.addEventListener('click', e => {
    if (!sidebar.contains(e.target) && !btn.contains(e.target)) {
      sidebar.classList.remove('open'); btn.classList.remove('open');
    }
  });
}

document.addEventListener('DOMContentLoaded', () => {
  initTabs(); initCopyButtons(); initScrollSpy(); initHamburger();
});
"""

# ==============================================================================
# HTML DOCUMENT (plain string concatenation — no f-strings)
# ==============================================================================

HTML = (
    '<!DOCTYPE html>\n'
    '<html lang="en">\n'
    '<head>\n'
    '<meta charset="UTF-8">\n'
    '<meta name="viewport" content="width=device-width, initial-scale=1.0">\n'
    '<title>Group 03 &mdash; PageRank Cluster Manual</title>\n'
    '<link rel="preconnect" href="https://fonts.googleapis.com">\n'
    '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
    '<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=Sora:wght@300;400;600;700;800&display=swap" rel="stylesheet">\n'
    '<style>\n' + CSS + '\n</style>\n'
    '</head>\n'
    '<body>\n'
    '<button class="hamburger" id="hamburger" aria-label="Toggle navigation">'
    '<span></span><span></span><span></span>'
    '</button>\n'
    '<div class="layout">\n'

    # Sidebar
    '<nav class="sidebar" id="sidebar">\n'
    '  <div class="sidebar-header">\n'
    '    <div class="sidebar-logo">Group 03</div>\n'
    '    <div class="sidebar-title">PageRank Cluster Manual</div>\n'
    '  </div>\n'
    '  <div class="toc">\n'
    '    <div class="toc-part">Part 1 &mdash; Master Setup</div>\n'
    '    <a class="toc-link" href="#s1-1">1.1 Prerequisites</a>\n'
    '    <a class="toc-link" href="#s1-2">1.2 Find Your LAN IP</a>\n'
    '    <a class="toc-link" href="#s1-3">1.3 Configure</a>\n'
    '    <a class="toc-link" href="#s1-4">1.4 Run Master Setup</a>\n'
    '    <a class="toc-link" href="#s1-5">1.5 Verify in Browser</a>\n'
    '    <a class="toc-link" href="#s1-6">1.6 Load the Dataset</a>\n'
    '    <a class="toc-link" href="#s1-7">1.7 Run PageRank</a>\n'
    '    <a class="toc-link" href="#s1-8">1.8 Start the API</a>\n'
    '    <div class="toc-part">Part 2 &mdash; Worker Setup</div>\n'
    '    <a class="toc-link" href="#s2-1">2.1 Before You Start</a>\n'
    '    <a class="toc-link" href="#s2-2">2.2 Clone and Configure</a>\n'
    '    <a class="toc-link" href="#s2-3">2.3 Run Worker Setup</a>\n'
    '    <a class="toc-link" href="#s2-4">2.4 Register with Master</a>\n'
    '    <a class="toc-link" href="#s2-5">2.5 Common Failures</a>\n'
    '    <div class="toc-part">Part 3 &mdash; Portability Test</div>\n'
    '    <a class="toc-link" href="#s3-1">3.1 Check Service is Up</a>\n'
    '    <a class="toc-link" href="#s3-2">3.2 Query Top 5 Results</a>\n'
    '    <a class="toc-link" href="#s3-3">3.3 Query a Specific Node</a>\n'
    '    <a class="toc-link" href="#s3-5">3.5 Top N Nodes</a>\n'
    '    <a class="toc-link" href="#s3-6">3.6 Outgoing Edges (Neighbors)</a>\n'
    '    <a class="toc-link" href="#s3-7">3.7 Incoming Edges (Influencers)</a>\n'
    '    <a class="toc-link" href="#s3-8">3.8 Job Statistics</a>\n'
    '    <a class="toc-link" href="#s3-9">3.9 Background Rerun</a>\n'
    '    <a class="toc-link" href="#s3-10">3.10 If Something Fails</a>\n'
    '  </div>\n'
    '</nav>\n'

    # Main
    '<main class="main">\n'

    # Cover
    '<div class="cover">\n'
    '  <div class="cover-inner">\n'
    '    <div class="cover-badge">GROUP 03 &middot; SECTION H3</div>\n'
    '    <h1>Network Graph<br>PageRank Cluster</h1>\n'
    '    <div class="cover-sub">Setup &amp; Portability Manual &mdash; ' + today + '</div>\n'
    '    <div class="cover-chips">\n'
    '      <span class="chip">Apache Spark 3.5.1</span>\n'
    '      <span class="chip">Hadoop HDFS 3.3.6</span>\n'
    '      <span class="chip">Stanford Web-Google</span>\n'
    '      <span class="chip">875K nodes &middot; 5M edges</span>\n'
    '      <span class="chip">macOS &middot; Linux &middot; Windows</span>\n'
    '    </div>\n'
    '  </div>\n'
    '</div>\n'

    '<div class="content">\n'

    + part_div(1, "Master Setup")
    + '<p style="color:var(--ink-3);font-size:13.5px;margin-top:12px;">Run these steps on the one machine that will act as the cluster coordinator &mdash; the <strong>master node</strong>. Other team members should skip to Part 2.</p>\n'
    + p1_s1 + p1_s2 + p1_s3 + p1_s4 + p1_s5 + p1_s6 + p1_s7 + p1_s8

    + part_div(2, "Worker Setup")
    + '<p style="color:var(--ink-3);font-size:13.5px;margin-top:12px;">Run these steps on every laptop that will join the cluster as a worker. The master must already be running (Part 1 complete) before you start here.</p>\n'
    + p2_s1 + p2_s2 + p2_s3 + p2_s4 + p2_s5

    + part_div(3, "Portability Test")
    + '<p style="color:var(--ink-3);font-size:13.5px;margin-top:12px;">These instructions are for the group that is <strong>testing Group 03\'s output</strong>. Follow them from any machine on the same LAN as the Group 03 master.</p>\n'
    + p3_intro + p3_s1 + p3_s2 + p3_s3 + p3_s4 + p3_s5 + p3_s6 + p3_s7 + p3_s8 + p3_s9 + p3_s10

    + '</div>\n'  # /content
    '<footer>Group 03 &mdash; Section H3 &mdash; ' + today + '</footer>\n'
    '</main>\n'
    '</div>\n'  # /layout
    '<script>\n' + JS + '\n</script>\n'
    '</body>\n'
    '</html>\n'
)

OUT = DOCS_DIR / "index.html"
OUT.write_text(HTML, encoding="utf-8")
print("✓ Manual generated: " + str(OUT))
print("  Size: " + "{:.1f}".format(OUT.stat().st_size / 1024) + " KB")
print("  Preview: python3 -m http.server 8888 --directory docs")
print("  Open:    http://localhost:8888/")

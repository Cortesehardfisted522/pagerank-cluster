#!/usr/bin/env python3
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

# Load actual results if available
top5 = []
top5_json_str = '[\n  "Run pagerank.py first to populate this"\n]'
if (DATA_DIR / "top5.json").exists():
    with open(DATA_DIR / "top5.json") as f:
        top5 = json.load(f)
    top5_json_str = json.dumps(top5, indent=2)

master_ip  = os.environ.get("MASTER_IP", "192.168.1.14")
today      = datetime.now().strftime("%B %d, %Y")
top_node   = top5[0]["nodeId"] if top5 else "41909"

# ── helpers ───────────────────────────────────────────────────────────────────

def cb(code: str, lang: str = "") -> str:
    """Wrap code in a copyable dark code block."""
    escaped = (code.replace("&", "&amp;")
                   .replace("<", "&lt;")
                   .replace(">", "&gt;"))
    return f"""<div class="code-wrap"><button class="copy-btn" aria-label="Copy code">Copy</button><pre><code class="lang-{lang}">{escaped}</code></pre></div>"""

def tabs(macos: str, linux: str, windows: str) -> str:
    """Three-tab OS switcher."""
    return f"""<div class="os-tabs">
  <div class="os-tab-bar" role="tablist">
    <button class="os-tab" role="tab" data-os="macos">macOS</button>
    <button class="os-tab" role="tab" data-os="linux">Linux</button>
    <button class="os-tab" role="tab" data-os="windows">Windows</button>
  </div>
  <div class="os-pane" data-os="macos">{cb(macos, "bash")}</div>
  <div class="os-pane" data-os="linux">{cb(linux, "bash")}</div>
  <div class="os-pane" data-os="windows">{cb(windows, "powershell")}</div>
</div>"""

def warn(title: str, body: str) -> str:
    return f'<div class="callout callout-warn"><span class="callout-icon">⚠</span><div><strong>{title}</strong>{body}</div></div>'

def tip(title: str, body: str) -> str:
    return f'<div class="callout callout-tip"><span class="callout-icon">💡</span><div><strong>{title}</strong>{body}</div></div>'

def expected(title: str, body: str) -> str:
    return f'<div class="callout callout-ok"><span class="callout-icon">✓</span><div><strong>{title}</strong>{body}</div></div>'

def section(id_: str, num: str, title: str, body: str) -> str:
    return f'<section id="{id_}"><h3><span class="sec-num">{num}</span>{title}</h3>{body}</section>'

def part_divider(num: int, title: str) -> str:
    return f"""<div class="part-divider" id="part{num}">
  <div class="part-label">Part {num}</div>
  <div class="part-title">{title}</div>
</div>"""

# ── top-5 table ───────────────────────────────────────────────────────────────
if top5:
    rows = "\n".join(
        f'<tr><td class="rank">#{e["rank"]}</td><td><code>{e["nodeId"]}</code></td><td class="score">{e["pagerank"]:.8f}</td></tr>'
        for e in top5
    )
    top5_table = f"""<table class="results-table">
  <thead><tr><th>Rank</th><th>Node ID</th><th>PageRank Score</th></tr></thead>
  <tbody>{rows}</tbody>
</table>"""
else:
    top5_table = '<p class="muted">Run <code>src/pagerank.py</code> first to populate results.</p>'

# ══════════════════════════════════════════════════════════════════════════════
# PART 1 CONTENT
# ══════════════════════════════════════════════════════════════════════════════

p1_s1 = section("s1-1", "1.1", "Prerequisites", f"""
<p>Before running anything, verify these three tools are installed. Every command below must succeed.</p>

<h4>Python 3.8+</h4>
{cb("python3 --version", "bash")}
{expected("Expected output", "<p><code>Python 3.10.12</code> (or any 3.8+). If you see <em>command not found</em>, install Python from <code>python.org</code>.</p>")}

<h4>Java 11</h4>
{cb("java -version", "bash")}
{expected("Expected output", "<p><code>openjdk version &quot;11.0.22&quot; 2024-01-16</code> — the word <em>11</em> must appear. Java 17 also works.</p>")}

<p>If Java is missing, install it now:</p>
{tabs(
    "brew install openjdk@11\n# Then add to your shell profile:\nexport PATH=\"$(brew --prefix openjdk@11)/bin:$PATH\"\nsource ~/.zprofile",
    "sudo apt-get update\nsudo apt-get install -y openjdk-11-jdk",
    "winget install EclipseAdoptium.Temurin.11.JDK --silent\n# Or download the .msi from: https://adoptium.net"
)}
{warn("Java version matters", "<p>Hadoop's startup scripts are sensitive to the Java version. Java 8 and Java 21+ both cause subtle failures. Stick to Java 11 (or 17 at most).</p>")}

<h4>Git</h4>
{cb("git --version", "bash")}
{expected("Expected output", "<p><code>git version 2.x.x</code>. If missing, install via <code>brew install git</code> (macOS), <code>sudo apt install git</code> (Linux), or from <code>git-scm.com</code> (Windows).</p>")}
""")

p1_s2 = section("s1-2", "1.2", "Find Your LAN IP", f"""
<p>Your LAN IP is the address other machines on the same Wi-Fi will use to reach yours. It usually starts with <code>192.168.</code> or <code>10.</code>.</p>
{tabs(
    "ipconfig getifaddr en0\n# Expected output example:\n# 192.168.1.14",
    "hostname -I | awk '{print $1}'\n# Expected output example:\n# 192.168.1.14",
    "(Get-NetIPAddress -AddressFamily IPv4 |\n  Where-Object { $_.IPAddress -like '192.168.*' }).IPAddress\n# Expected output example:\n# 192.168.1.14"
)}
{tip("Can't find your IP?", "<p>Make sure your machine is connected to the same Wi-Fi as the other nodes. Ethernet connections may show up on <code>en1</code> (macOS) or <code>eth0</code> (Linux) instead.</p>")}
""")

p1_s3 = section("s1-3", "1.3", "Configure", f"""
<p>Open <code>setup/config.py</code>. There is exactly one line you need to change — <code>MASTER_IP</code>. Everything else is auto-detected.</p>

<p><strong>Before</strong> (the default placeholder):</p>
{cb('MASTER_IP = "192.168.1.14"   # ← set to master laptop\'s LAN IP', "python")}

<p><strong>After</strong> (your actual LAN IP from Section 1.2):</p>
{cb('MASTER_IP = "192.168.1.42"   # ← your actual LAN IP here', "python")}

{warn("Set this before running anything", "<p>Every setup script imports <code>config.py</code>. If <code>MASTER_IP</code> is wrong, Hadoop and Spark will start but workers will be unable to connect — and the error messages won't point here.</p>")}

<p>Verify the config loads cleanly:</p>
{cb("python3 setup/config.py", "bash")}
{expected("Expected output", f"<pre>OS          : Darwin\nLocal IP    : 192.168.1.42\nMASTER_IP   : 192.168.1.42\nJAVA_HOME   : /opt/homebrew/opt/openjdk@11\nHADOOP_HOME : /opt/homebrew/Cellar/hadoop/3.5.0/libexec\nSPARK_HOME  : /opt/spark-3.5.1\n  ✓ Java: openjdk version \"11.0.22\" 2024-01-16</pre>")}
""")

p1_s4 = section("s1-4", "1.4", "Run Master Setup", f"""
<p>This single command installs Hadoop (a distributed filesystem) and Spark (a distributed computation engine), formats the filesystem, and starts all required services.</p>

{cb("python3 setup/setup_node.py --role master", "bash")}

<p>The script prints phases as it runs. Here is what each one means:</p>
<table>
  <thead><tr><th>Phase printed</th><th>What is happening</th></tr></thead>
  <tbody>
    <tr><td><code>── Java 11 ──</code></td><td>Checks Java is present; installs if missing.</td></tr>
    <tr><td><code>── Python dependencies ──</code></td><td>Installs <code>pyspark</code>, <code>flask</code>, <code>requests</code> via pip.</td></tr>
    <tr><td><code>── Hadoop 3.3.6 (master) ──</code></td><td>Downloads ~650 MB Hadoop archive and extracts it. Writes XML config files pointing at your <code>MASTER_IP</code>.</td></tr>
    <tr><td><code>── Spark 3.5.1 (master) ──</code></td><td>Downloads ~300 MB Spark archive and extracts it. Writes <code>spark-defaults.conf</code>.</td></tr>
    <tr><td><code>── Formatting NameNode ──</code></td><td>Initialises the HDFS metadata directory. Only happens once; skipped on re-runs.</td></tr>
    <tr><td><code>── Starting services (master) ──</code></td><td>Launches NameNode, DataNode, SecondaryNameNode, and Spark Master as background daemons.</td></tr>
    <tr><td><code>── Verification ──</code></td><td>Runs <code>jps</code> to list running Java processes and confirms all four are present.</td></tr>
  </tbody>
</table>

{tip("This takes a while the first time", "<p>Downloading Hadoop + Spark is about 1 GB total. On a fast connection expect 3–5 minutes; on a slow one, up to 20. Subsequent runs skip the download.</p>")}

<h4>After it finishes: check with <code>jps</code></h4>
<p><code>jps</code> — the Java Virtual Machine Process Status tool — lists every running Java process. After master setup you should see exactly four:</p>
{cb("jps", "bash")}
{expected("Expected output — all four must appear", """<pre>12345 NameNode
12346 DataNode
12347 SecondaryNameNode
12348 Master
12349 Jps</pre>""")}

<p>If a process is missing, here is where to look:</p>
<table>
  <thead><tr><th>Missing process</th><th>What to check</th></tr></thead>
  <tbody>
    <tr><td><code>NameNode</code></td><td>Check <code>/opt/homebrew/Cellar/hadoop/3.5.0/libexec/logs/hadoop-*-namenode-*.log</code>. Common cause: wrong <code>JAVA_HOME</code> in <code>hadoop-env.sh</code>.</td></tr>
    <tr><td><code>DataNode</code></td><td>Usually starts after NameNode. If NameNode is up but DataNode isn't, check for port 9000 conflicts: <code>lsof -i :9000</code>.</td></tr>
    <tr><td><code>SecondaryNameNode</code></td><td>Non-critical for this lab. Its absence won't block PageRank.</td></tr>
    <tr><td><code>Master</code> (Spark)</td><td>Check <code>/opt/spark-3.5.1/logs/spark-*-org.apache.spark.deploy.master.Master-*.out</code>.</td></tr>
  </tbody>
</table>
""")

p1_s5 = section("s1-5", "1.5", "Verify in Browser", f"""
<p>Two web UIs start automatically. Open them to confirm the cluster is healthy.</p>

<h4>Spark UI — <code>http://{master_ip}:8080</code></h4>
<p>You should see the Spark Master dashboard. Look for: <strong>Status: ALIVE</strong> and at least one worker listed under "Workers" (the master itself counts as a worker at this stage).</p>

<h4>HDFS NameNode UI — <code>http://{master_ip}:9870</code></h4>
<p>You should see the Hadoop NameNode overview. Look for: <strong>Live Nodes: 1</strong> (or more once workers join) and <strong>Safe Mode: OFF</strong>.</p>

{warn("If the browser just times out", """<p>The ports are blocked by a firewall. Open them:</p>""")}

{tabs(
    "# macOS — allow incoming on these ports\nsudo /usr/libexec/ApplicationFirewall/socketfilterfw --add /usr/bin/java\n# Or turn off the firewall temporarily:\nsudo /usr/libexec/ApplicationFirewall/socketfilterfw --setglobalstate off",
    "# Linux (ufw)\nsudo ufw allow 8080\nsudo ufw allow 9870\nsudo ufw allow 9000\nsudo ufw allow 7077\nsudo ufw allow 5000",
    "# Windows PowerShell (run as Administrator)\nnetsh advfirewall firewall add rule name=\"Spark\" dir=in action=allow protocol=TCP localport=8080\nnetsh advfirewall firewall add rule name=\"HDFS\" dir=in action=allow protocol=TCP localport=9870\nnetsh advfirewall firewall add rule name=\"SparkMaster\" dir=in action=allow protocol=TCP localport=7077"
)}
""")

p1_s6 = section("s1-6", "1.6", "Load the Dataset", f"""
<p>The dataset is the Stanford Web-Google graph — a snapshot of 875,713 web pages and 5,105,039 hyperlinks between them, collected by Google in 2002. HDFS (the Hadoop Distributed File System) stores data across all nodes so Spark can read it in parallel.</p>

<h4>Step 1 — Download</h4>
{cb("python3 src/download_dataset.py", "bash")}
{expected("Expected output", """<pre>Downloading from https://snap.stanford.edu/data/web-Google.txt.gz ...
  [████████████████████] 100%
Extracting...

✓ Ready: data/web-Google.txt
  Nodes: 875,713
  Edges: 5,105,039

Next: hdfs dfs -put data/web-Google.txt /pagerank/input/</pre>""")}

<h4>Step 2 — Push to HDFS</h4>
<p><code>hdfs dfs -put</code> copies a local file into the distributed filesystem so all workers can access it.</p>
{cb("hdfs dfs -put data/web-Google.txt /pagerank/input/", "bash")}
{expected("Expected output", "<p>No output means success. Verify the file landed:</p><pre>hdfs dfs -ls /pagerank/input/\n\n-rw-r--r--   2 user supergroup  804298888 2024-05-09 /pagerank/input/web-Google.txt</pre>")}

{tip("Already in HDFS?", "<p>If you re-run, use <code>hdfs dfs -put -f</code> (force overwrite) to replace an existing file.</p>")}
""")

p1_s7 = section("s1-7", "1.7", "Run PageRank", f"""
<p>This submits the PageRank job to Spark. <code>spark-submit</code> packages your Python script and sends it to the Spark Master, which distributes the computation across all connected workers.</p>

{cb(f"spark-submit \\\n  --master spark://{master_ip}:7077 \\\n  --executor-memory 2g \\\n  --driver-memory 1g \\\n  src/pagerank.py 10", "bash")}

<p>The number <code>10</code> is the iteration count. During the run you will see lines like:</p>
{expected("Iteration output", """<pre>  Iteration  1/10  12.3s
  Iteration  2/10  11.8s
  Iteration  3/10  11.5s
  ...
  Iteration 10/10  11.2s

Collecting results...

═══════════════════════════════════════════════════════
  TOP 5 MOST INFLUENTIAL NODES
═══════════════════════════════════════════════════════
  #1  node      41909  →  445.71778597
  #2  node     597621  →  406.62836675
  #3  node     504140  →  399.08930875
  #4  node     384666  →  392.82584373
  #5  node     537039  →  383.90912550
═══════════════════════════════════════════════════════

✓ Done in 118.4s</pre>""")}

<p>Each iteration line shows the wall-clock time for one pass over the graph. Times should be roughly stable; a sudden spike usually means a worker disconnected.</p>

<h4>Where results are saved</h4>
<table>
  <thead><tr><th>File</th><th>Contents</th></tr></thead>
  <tbody>
    <tr><td><code>data/top5.json</code></td><td>Top 5 nodes — this is what the API serves.</td></tr>
    <tr><td><code>data/results.json</code></td><td>Top 1000 nodes with scores, for <code>/node/&lt;id&gt;</code> queries.</td></tr>
    <tr><td><code>data/pagerank_output/part-00000</code></td><td>All nodes, tab-separated: <code>nodeId\tscore</code>.</td></tr>
  </tbody>
</table>
""")

p1_s8 = section("s1-8", "1.8", "Start the API", f"""
<p>The REST API is a small Flask server that reads <code>data/top5.json</code> and serves it to other groups over HTTP.</p>

<h4>Verify locally first</h4>
{cb("python3 src/api.py", "bash")}
{expected("Expected startup output", f"""<pre>══════════════════════════════════════════════════
  Group 03 · PageRank Portability API
  http://{master_ip}:5000

  GET /top5          → top 5 influencers
  GET /node/&lt;id&gt;     → score for node id
  GET /health        → status check

  ✓ Results loaded — top node: 41909 (445.71778597)
══════════════════════════════════════════════════</pre>""")}

<p>In a second terminal, confirm it responds:</p>
{cb(f"curl http://localhost:5000/health", "bash")}

<h4>Run it in the background (so you can close the terminal)</h4>
{tabs(
    f"nohup python3 src/api.py > /tmp/api.log 2>&1 &\necho \"API PID: $!\"\n# To stop it later:\n# kill $(lsof -ti :5000)",
    f"nohup python3 src/api.py > /tmp/api.log 2>&1 &\necho \"API PID: $!\"\n# To stop it later:\n# kill $(lsof -ti :5000)",
    f"# PowerShell — start as a background job\nStart-Job -ScriptBlock {{ python3 src/api.py }} | Out-Null\nWrite-Host 'API started in background'\n# To stop: Get-Job | Stop-Job"
)}

<h4>Three ways to verify it works</h4>
{cb(f"# Option 1 — curl\ncurl http://localhost:5000/health\n\n# Option 2 — Python (works on all three OS)\npython3 -c \"import urllib.request, json; print(json.loads(urllib.request.urlopen('http://localhost:5000/health').read()))\"\n\n# Option 3 — Browser\n# Open: http://localhost:5000/health", "bash")}

{tip("macOS port 5000 conflict", "<p>macOS Monterey+ reserves port 5000 for AirPlay Receiver. If <code>curl</code> returns <em>connection refused</em>, go to <strong>System Settings → AirDrop &amp; Handoff</strong> and turn off AirPlay Receiver. Then restart the API.</p>")}
""")

# ══════════════════════════════════════════════════════════════════════════════
# PART 2 CONTENT
# ══════════════════════════════════════════════════════════════════════════════

p2_s1 = section("s2-1", "2.1", "Before You Start", f"""
<p>The master node must be fully running before you set up any worker. Specifically:</p>
<ul>
  <li>Section 1.4 must be complete — <code>jps</code> on the master shows all four processes.</li>
  <li>You need the master's LAN IP address from Section 1.2.</li>
  <li>Both machines must be on the same Wi-Fi or wired LAN.</li>
</ul>
{cb(f"# Quick connectivity check from the worker machine:\nping -c 3 {master_ip}\n# All 3 packets should receive a reply.", "bash")}
{warn("Different Wi-Fi networks", "<p>University campuses often have network isolation between clients on the same SSID. If ping fails even though you're on the same network, use a personal hotspot or a wired switch shared between the machines.</p>")}
""")

p2_s2 = section("s2-2", "2.2", "Clone and Configure", f"""
<h4>Clone the repository on the worker machine</h4>
{cb("git clone https://github.com/your-group/pagerank-cluster\ncd pagerank-cluster", "bash")}

<h4>Set <code>MASTER_IP</code> in <code>setup/config.py</code></h4>
<p>Open the file and change the one line:</p>
{cb('MASTER_IP = "192.168.1.42"   # ← the MASTER\'s LAN IP, NOT your own', "python")}

{warn("Common mistake — setting MASTER_IP to your own IP on a worker machine", "<p>On the <strong>worker</strong>, <code>MASTER_IP</code> must be the IP of the <strong>master laptop</strong>, not the worker's own IP. If you set it to your own IP, the worker will try to connect to itself as a master — and fail silently. Double-check before running setup.</p>")}
""")

p2_s3 = section("s2-3", "2.3", "Run Worker Setup", f"""
{cb("python3 setup/setup_node.py --role worker", "bash")}

<p>This installs Java, Python dependencies, Hadoop, and Spark — same as the master, but starts only the DataNode and Spark Worker daemons (not the NameNode or Spark Master).</p>

<h4>After it finishes: check with <code>jps</code></h4>
{cb("jps", "bash")}
{expected("Expected output on the worker — exactly these two", """<pre>23456 DataNode
23457 Worker
23458 Jps</pre><p>You should <strong>not</strong> see <code>NameNode</code> or <code>Master</code> on a worker — those only run on the master machine.</p>""")}
""")

p2_s4 = section("s2-4", "2.4", "Register with Master", f"""
<p>The master needs to know this worker exists. This is a two-step handshake: the worker reports its IP, then the master adds it to the cluster roster.</p>

<h4>Step 1 — Find your own IP (on the worker machine)</h4>
{tabs(
    "ipconfig getifaddr en0",
    "hostname -I | awk '{print $1}'",
    "(Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.IPAddress -like '192.168.*' }).IPAddress"
)}

<h4>Step 2 — Send your IP to the master operator</h4>
<p>Tell the person running the master laptop your IP (e.g., via Slack, Discord, or just say it out loud). They run this on the master:</p>
{cb("# On the MASTER machine — replace with the worker's actual IP\npython3 setup/register_worker.py 192.168.1.55", "bash")}

<h4>Step 3 — Verify from the master</h4>
{cb("hdfs dfsadmin -report | grep 'Live datanodes'", "bash")}
{expected("Expected output", "<p><code>Live datanodes (2):</code> — the count increases by 1 each time a worker is registered. If you have 1 worker plus the master's own DataNode, you'll see 2.</p>")}
""")

p2_s5 = section("s2-5", "2.5", "Most Common Failures", f"""
<h4>Failure 1 — <code>MASTER_IP</code> mismatch</h4>
<p>The worker starts but never appears in the Spark UI or HDFS report.</p>
{expected("What the error looks like in Spark Worker logs", """<pre>ERROR Worker: All masters are unresponsive! Giving up.
ERROR Worker: Connection to spark://192.168.1.99:7077 failed</pre>""")}
<p><strong>Fix:</strong> Open <code>setup/config.py</code> on the <em>worker</em> machine and correct <code>MASTER_IP</code> to the master's actual LAN IP. Then re-run worker setup.</p>

<h4>Failure 2 — Worker can't reach master (firewall)</h4>
<p>Ping succeeds but Spark/HDFS connections time out.</p>
{tabs(
    "# macOS — allow Java through the firewall\nsudo /usr/libexec/ApplicationFirewall/socketfilterfw --add /usr/bin/java\n# Or disable the firewall temporarily for the session:\nsudo /usr/libexec/ApplicationFirewall/socketfilterfw --setglobalstate off",
    "sudo ufw allow from 192.168.1.0/24\n# Or open specific ports:\nsudo ufw allow 7077\nsudo ufw allow 9000\nsudo ufw allow 9866",
    "# Run as Administrator\nnetsh advfirewall firewall add rule name=\"Hadoop-Spark\" dir=in action=allow protocol=TCP localport=7077,9000,9866,9870"
)}
""")

# ══════════════════════════════════════════════════════════════════════════════
# PART 3 CONTENT
# ══════════════════════════════════════════════════════════════════════════════

p3_intro = f"""<p>The portability test checks that your group's API can be queried by a <em>different</em> group's machine — confirming the result is not just local but genuinely accessible over the LAN. You are querying the Group 03 master node for the top-5 most influential pages in the Stanford Web-Google graph, as computed by our distributed PageRank job. The three endpoints below must all return valid JSON.</p>"""

p3_s1 = section("s3-1", "3.1", "Check the Service Is Up", f"""
<p>Before querying results, confirm the API process is alive.</p>

<h4>Three ways to call <code>GET /health</code></h4>
{cb(f"# curl\ncurl http://{master_ip}:5000/health\n\n# Python\npython3 -c \"import urllib.request, json; print(json.dumps(json.loads(urllib.request.urlopen('http://{master_ip}:5000/health').read()), indent=2))\"\n\n# Browser\n# http://{master_ip}:5000/health", "bash")}

{expected("Healthy response", f"""<pre>{{
  \"dataset\": \"Stanford Web-Google\",
  \"framework\": \"Apache Spark\",
  \"group\": \"03\",
  \"results_ready\": true,
  \"status\": \"ok\",
  \"task\": \"Network Graph PageRank\"
}}</pre>""")}

{warn("Failed / unexpected response", """<p>If the connection is refused: the API process isn't running. Contact the Group 03 master operator to restart it (<code>python3 src/api.py &amp;</code>).</p><p>If you get a timeout: check network connectivity with <code>ping</code> first, then check firewall rules (Section 2.5).</p>""")}
""")

_top5_query_code = "\n".join([
    "# curl",
    f"curl http://{master_ip}:5000/top5",
    "",
    "# Python urllib (no extra libraries needed)",
    "python3 -c \"",
    "import urllib.request, json",
    f"data = json.loads(urllib.request.urlopen('http://{master_ip}:5000/top5').read())",
    "for n in data:",
    "    print(n['rank'], n['nodeId'], n['pagerank'])",
    "\"",
    "",
    "# Browser",
    f"# http://{master_ip}:5000/top5",
])

p3_s2 = section("s3-2", "3.2", "Query the Top 5 Results", f"""
<p><code>GET /top5</code> returns the five highest-ranked nodes in the Web-Google graph.</p>

{cb(_top5_query_code, "bash")}

{expected("Expected JSON response", f"<pre>{top5_json_str}</pre>")}

{tip("Scores may differ slightly", "<p>PageRank scores depend on the number of iterations and the damping factor. Our run used 10 iterations and damping 0.85. Node IDs will match; the exact floating-point values may vary by ±0.001 if you re-run with different settings.</p>")}
""")

p3_s3 = section("s3-3", "3.3", "Query a Specific Node", f"""
<p><code>GET /node/&lt;id&gt;</code> returns the score for one node. Use the top-ranked node's ID as your test case.</p>

{cb(f"# curl — query the top node\ncurl http://{master_ip}:5000/node/{top_node}\n\n# Python\npython3 -c \"\nimport urllib.request, json\ndata = json.loads(urllib.request.urlopen('http://{master_ip}:5000/node/{top_node}').read())\nprint(json.dumps(data, indent=2))\n\"", "bash")}

{expected("Expected response", f"""<pre>{{
  \"nodeId\": \"{top_node}\",
  \"pagerank\": {top5[0]['pagerank'] if top5 else 445.71778597}
}}</pre>""")}
""")

p3_s4 = section("s3-4", "3.4", "If Something Fails", f"""
<h4>API unreachable (connection refused / timeout)</h4>
<p>Step 1: confirm basic network connectivity first.</p>
{cb(f"ping -c 4 {master_ip}", "bash")}
<p>If ping fails, you are on different networks. If ping succeeds but the API is still unreachable, the firewall is blocking port 5000. Apply the firewall rules from Section 2.5 on the <strong>master</strong> machine.</p>

<h4>503 response — results not ready</h4>
{expected("503 response body", '<pre>{"error": "Results not ready. Run src/pagerank.py first."}</pre><p>The PageRank job has not finished yet (or has not been run at all). Contact the Group 03 master operator. Do not mark the portability test as failed immediately — the job takes approximately 2 minutes to complete.</p>')}

<h4>404 on a node ID</h4>
{expected("404 response body", '<pre>{"error": "Node \'999999\' not in top-1000 results."}</pre><p>The API only stores the top 1000 nodes by PageRank score. A 404 for a node ID that is not in the top 1000 is expected and correct behaviour — it does not indicate a bug.</p>')}
""")

# ══════════════════════════════════════════════════════════════════════════════
# HTML DOCUMENT
# ══════════════════════════════════════════════════════════════════════════════

HTML = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Group 03 — PageRank Cluster Manual</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=Sora:wght@300;400;600;700;800&display=swap" rel="stylesheet">
<style>
/* ── Reset & Tokens ─────────────────────────────────────────────────────── */
*, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

:root {{
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
}}

html {{ scroll-behavior: smooth; }}
body {{
  font-family: var(--sans);
  background: var(--canvas);
  color: var(--ink);
  line-height: 1.75;
  font-size: 15px;
  font-weight: 300;
}}

/* ── Layout ─────────────────────────────────────────────────────────────── */
.layout {{
  display: flex;
  min-height: 100vh;
}}

.sidebar {{
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
}}

.main {{
  flex: 1;
  min-width: 0;
  padding: 0 clamp(20px, 5vw, 80px) 100px;
}}

.content {{
  max-width: var(--content-w);
  margin: 0 auto;
}}

/* ── Sidebar internals ──────────────────────────────────────────────────── */
.sidebar-header {{
  padding: 24px 20px 16px;
  border-bottom: 1px solid var(--border);
}}
.sidebar-logo {{
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 2px;
  text-transform: uppercase;
  color: var(--ink-3);
  margin-bottom: 4px;
}}
.sidebar-title {{
  font-size: 13px;
  font-weight: 700;
  color: var(--ink);
  line-height: 1.3;
}}

.toc {{
  padding: 16px 0 24px;
  flex: 1;
}}
.toc-part {{
  padding: 8px 20px 4px;
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 2px;
  text-transform: uppercase;
  color: var(--ink-3);
  margin-top: 8px;
}}
.toc-link {{
  display: block;
  padding: 5px 20px 5px 28px;
  font-size: 12.5px;
  color: var(--ink-2);
  text-decoration: none;
  border-left: 2px solid transparent;
  transition: all 0.15s;
  line-height: 1.4;
}}
.toc-link:hover {{
  color: var(--accent);
  background: var(--accent-dim);
}}
.toc-link.active {{
  color: var(--accent);
  border-left-color: var(--accent);
  background: var(--accent-dim);
  font-weight: 600;
}}

/* Hamburger */
.hamburger {{
  display: none;
  position: fixed;
  top: 16px;
  left: 16px;
  z-index: 200;
  width: 40px;
  height: 40px;
  background: var(--ink);
  border: none;
  border-radius: var(--r);
  cursor: pointer;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 5px;
  transition: background 0.2s;
}}
.hamburger span {{
  display: block;
  width: 20px;
  height: 2px;
  background: #fff;
  border-radius: 2px;
  transition: all 0.25s;
}}
.hamburger.open span:nth-child(1) {{ transform: translateY(7px) rotate(45deg); }}
.hamburger.open span:nth-child(2) {{ opacity: 0; }}
.hamburger.open span:nth-child(3) {{ transform: translateY(-7px) rotate(-45deg); }}

/* ── Cover ──────────────────────────────────────────────────────────────── */
.cover {{
  background: var(--ink);
  color: #fff;
  padding: 72px 0 64px;
  margin-bottom: 0;
}}
.cover-inner {{
  max-width: var(--content-w);
  margin: 0 auto;
}}
.cover-badge {{
  display: inline-block;
  font-family: var(--mono);
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 1.5px;
  background: rgba(255,255,255,0.1);
  border: 1px solid rgba(255,255,255,0.2);
  border-radius: 4px;
  padding: 3px 10px;
  margin-bottom: 24px;
  color: rgba(255,255,255,0.7);
}}
.cover h1 {{
  font-size: clamp(28px, 5vw, 46px);
  font-weight: 800;
  line-height: 1.1;
  letter-spacing: -1.5px;
  margin-bottom: 12px;
}}
.cover-sub {{
  font-size: 15px;
  color: rgba(255,255,255,0.55);
  margin-bottom: 36px;
  font-weight: 300;
}}
.cover-chips {{
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}}
.chip {{
  font-family: var(--mono);
  font-size: 11px;
  background: rgba(255,255,255,0.07);
  border: 1px solid rgba(255,255,255,0.15);
  padding: 4px 12px;
  border-radius: 20px;
  color: rgba(255,255,255,0.6);
}}

/* ── Part divider ───────────────────────────────────────────────────────── */
.part-divider {{
  margin: 72px 0 0;
  padding: 36px 0 32px;
  border-top: 2px solid var(--border-2);
  position: relative;
}}
.part-divider::before {{
  content: '';
  position: absolute;
  top: -2px;
  left: 0;
  width: 60px;
  height: 2px;
  background: var(--accent);
}}
.part-label {{
  font-family: var(--mono);
  font-size: 11px;
  letter-spacing: 2px;
  text-transform: uppercase;
  color: var(--accent);
  margin-bottom: 6px;
}}
.part-title {{
  font-size: clamp(22px, 4vw, 32px);
  font-weight: 800;
  letter-spacing: -0.5px;
  color: var(--ink);
  line-height: 1.15;
}}

/* ── Sections ───────────────────────────────────────────────────────────── */
section {{
  margin-top: 52px;
  padding-top: 8px;
}}
section h3 {{
  font-size: 18px;
  font-weight: 700;
  color: var(--ink);
  margin-bottom: 16px;
  display: flex;
  align-items: baseline;
  gap: 12px;
}}
.sec-num {{
  font-family: var(--mono);
  font-size: 12px;
  color: var(--ink-3);
  font-weight: 600;
  flex-shrink: 0;
}}
h4 {{
  font-size: 13.5px;
  font-weight: 700;
  color: var(--ink);
  margin: 24px 0 8px;
  letter-spacing: 0.1px;
}}
p {{
  margin-bottom: 12px;
  color: var(--ink-2);
}}
ul, ol {{
  padding-left: 20px;
  margin-bottom: 14px;
  color: var(--ink-2);
}}
li {{ margin-bottom: 6px; }}
code {{
  font-family: var(--mono);
  font-size: 12.5px;
  background: var(--surface-2);
  color: #b91c1c;
  padding: 1px 5px;
  border-radius: 3px;
}}

/* ── Code blocks ────────────────────────────────────────────────────────── */
.code-wrap {{
  position: relative;
  margin: 12px 0 20px;
}}
.code-wrap pre {{
  background: var(--code-bg);
  border: 1px solid var(--code-border);
  border-radius: var(--r);
  padding: 18px 20px;
  overflow-x: auto;
  font-family: var(--mono);
  font-size: 12.5px;
  line-height: 1.65;
  color: var(--code-text);
  tab-size: 2;
}}
.code-wrap pre code {{
  background: none;
  color: inherit;
  padding: 0;
  font-size: inherit;
  border-radius: 0;
}}
.copy-btn {{
  position: absolute;
  top: 10px;
  right: 10px;
  font-family: var(--mono);
  font-size: 11px;
  font-weight: 600;
  color: #9ca3af;
  background: #1f2937;
  border: 1px solid #374151;
  border-radius: 4px;
  padding: 3px 10px;
  cursor: pointer;
  transition: all 0.15s;
  z-index: 2;
  letter-spacing: 0.3px;
}}
.copy-btn:hover {{
  background: #374151;
  color: #f9fafb;
  border-color: #4b5563;
}}
.copy-btn.copied {{
  color: #34d399;
  border-color: #34d399;
}}

/* ── OS Tabs ────────────────────────────────────────────────────────────── */
.os-tabs {{
  margin: 12px 0 20px;
  border: 1px solid var(--border);
  border-radius: var(--r);
  overflow: hidden;
}}
.os-tab-bar {{
  display: flex;
  background: var(--surface);
  border-bottom: 1px solid var(--border);
}}
.os-tab {{
  font-family: var(--mono);
  font-size: 11.5px;
  font-weight: 600;
  padding: 8px 18px;
  background: none;
  border: none;
  border-right: 1px solid var(--border);
  color: var(--ink-3);
  cursor: pointer;
  transition: all 0.15s;
  letter-spacing: 0.3px;
}}
.os-tab:last-child {{ border-right: none; }}
.os-tab:hover {{ background: var(--surface-2); color: var(--ink); }}
.os-tab.active {{
  background: var(--canvas);
  color: var(--accent);
  border-bottom: 2px solid var(--accent);
  margin-bottom: -1px;
}}
.os-pane {{ display: none; }}
.os-pane.active {{ display: block; }}
.os-pane .code-wrap {{ margin: 0; }}
.os-pane .code-wrap pre {{
  border: none;
  border-radius: 0;
}}

/* ── Callouts ───────────────────────────────────────────────────────────── */
.callout {{
  display: flex;
  gap: 12px;
  padding: 14px 16px;
  border-radius: var(--r);
  margin: 16px 0;
  border: 1px solid;
}}
.callout-warn {{
  background: var(--warn-bg);
  border-color: var(--warn-border);
  color: var(--warn);
}}
.callout-ok {{
  background: var(--ok-bg);
  border-color: var(--ok-border);
  color: var(--ok);
}}
.callout-tip {{
  background: var(--tip-bg);
  border-color: var(--tip-border);
  color: var(--tip);
}}
.callout-icon {{
  font-size: 15px;
  flex-shrink: 0;
  margin-top: 1px;
}}
.callout strong {{
  display: block;
  font-size: 13px;
  font-weight: 700;
  margin-bottom: 4px;
}}
.callout p {{ margin: 0; font-size: 13.5px; line-height: 1.6; color: inherit; }}
.callout pre {{
  background: rgba(0,0,0,0.06);
  border: none;
  border-radius: 4px;
  padding: 10px 12px;
  margin-top: 8px;
  font-size: 12px;
  line-height: 1.5;
  color: inherit;
  overflow-x: auto;
  font-family: var(--mono);
}}
.callout code {{
  background: rgba(0,0,0,0.08);
  color: inherit;
  padding: 1px 4px;
}}

/* ── Tables ─────────────────────────────────────────────────────────────── */
table {{
  width: 100%;
  border-collapse: collapse;
  margin: 16px 0 24px;
  font-size: 13.5px;
}}
thead tr {{
  background: var(--ink);
  color: #fff;
}}
th {{
  text-align: left;
  padding: 10px 14px;
  font-weight: 600;
  font-size: 12px;
  letter-spacing: 0.3px;
  white-space: nowrap;
}}
td {{
  padding: 9px 14px;
  border-bottom: 1px solid var(--border);
  vertical-align: top;
  color: var(--ink-2);
  line-height: 1.55;
}}
tr:last-child td {{ border-bottom: none; }}
tbody tr:hover td {{ background: var(--surface); }}
.results-table .rank {{ font-family: var(--mono); font-weight: 600; color: var(--ink); }}
.results-table .score {{ font-family: var(--mono); color: var(--accent); }}

/* ── Misc ───────────────────────────────────────────────────────────────── */
.muted {{ color: var(--ink-3); font-style: italic; }}

/* ── Footer ─────────────────────────────────────────────────────────────── */
footer {{
  margin-top: 80px;
  padding: 32px 0;
  border-top: 1px solid var(--border);
  font-size: 12px;
  color: var(--ink-3);
  font-family: var(--mono);
  text-align: center;
}}

/* ── Print ──────────────────────────────────────────────────────────────── */
@media print {{
  .sidebar, .hamburger {{ display: none !important; }}
  .layout {{ display: block; }}
  .main {{ padding: 0; }}
  .content {{ max-width: 100%; }}
  .cover {{ background: #000 !important; -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
  .code-wrap pre {{
    background: #111 !important;
    color: #e5e7eb !important;
    -webkit-print-color-adjust: exact;
    print-color-adjust: exact;
    white-space: pre-wrap;
    word-break: break-word;
  }}
  .copy-btn {{ display: none; }}
  .os-tabs .os-pane {{ display: block !important; }}
  .os-tabs .os-pane .code-wrap pre {{ border-top: 1px solid #374151; }}
  .os-tab-bar {{ display: none; }}
  section {{ page-break-inside: avoid; }}
  .part-divider {{ page-break-before: always; }}
}}

/* ── Responsive ─────────────────────────────────────────────────────────── */
@media (max-width: 900px) {{
  .hamburger {{ display: flex; }}
  .sidebar {{
    position: fixed;
    left: -100%;
    top: 0;
    height: 100vh;
    transition: left 0.25s ease;
    box-shadow: 4px 0 30px rgba(0,0,0,0.12);
  }}
  .sidebar.open {{ left: 0; }}
  .main {{ padding-top: 60px; }}
}}
</style>
</head>
<body>

<button class="hamburger" id="hamburger" aria-label="Toggle navigation">
  <span></span><span></span><span></span>
</button>

<div class="layout">

<!-- ── Sidebar ─────────────────────────────────────────────────────────── -->
<nav class="sidebar" id="sidebar">
  <div class="sidebar-header">
    <div class="sidebar-logo">FIT3143 · Group 03</div>
    <div class="sidebar-title">PageRank Cluster Manual</div>
  </div>
  <div class="toc">
    <div class="toc-part">Part 1 — Master Setup</div>
    <a class="toc-link" href="#s1-1">1.1 Prerequisites</a>
    <a class="toc-link" href="#s1-2">1.2 Find Your LAN IP</a>
    <a class="toc-link" href="#s1-3">1.3 Configure</a>
    <a class="toc-link" href="#s1-4">1.4 Run Master Setup</a>
    <a class="toc-link" href="#s1-5">1.5 Verify in Browser</a>
    <a class="toc-link" href="#s1-6">1.6 Load the Dataset</a>
    <a class="toc-link" href="#s1-7">1.7 Run PageRank</a>
    <a class="toc-link" href="#s1-8">1.8 Start the API</a>

    <div class="toc-part">Part 2 — Worker Setup</div>
    <a class="toc-link" href="#s2-1">2.1 Before You Start</a>
    <a class="toc-link" href="#s2-2">2.2 Clone and Configure</a>
    <a class="toc-link" href="#s2-3">2.3 Run Worker Setup</a>
    <a class="toc-link" href="#s2-4">2.4 Register with Master</a>
    <a class="toc-link" href="#s2-5">2.5 Common Failures</a>

    <div class="toc-part">Part 3 — Portability Test</div>
    <a class="toc-link" href="#s3-1">3.1 Check Service is Up</a>
    <a class="toc-link" href="#s3-2">3.2 Query Top 5 Results</a>
    <a class="toc-link" href="#s3-3">3.3 Query a Specific Node</a>
    <a class="toc-link" href="#s3-4">3.4 If Something Fails</a>
  </div>
</nav>

<!-- ── Main ────────────────────────────────────────────────────────────── -->
<main class="main">

<!-- Cover -->
<div class="cover">
  <div class="cover-inner">
    <div class="cover-badge">GROUP 03 · PARALLEL COMPUTING</div>
    <h1>Network Graph<br>PageRank Cluster</h1>
    <div class="cover-sub">Setup &amp; Portability Manual &mdash; {today}</div>
    <div class="cover-chips">
      <span class="chip">Apache Spark 3.5.1</span>
      <span class="chip">Hadoop HDFS 3.3.6</span>
      <span class="chip">Stanford Web-Google</span>
      <span class="chip">875K nodes · 5M edges</span>
      <span class="chip">macOS · Linux · Windows</span>
    </div>
  </div>
</div>

<div class="content">

<!-- ═══════════════════ PART 1 ═══════════════════ -->
{part_divider(1, "Master Setup")}
<p style="color:var(--ink-3);font-size:13.5px;margin-top:12px;">Run these steps on the one machine that will act as the cluster coordinator — the <strong>master node</strong>. Other team members should skip to Part 2.</p>

{p1_s1}
{p1_s2}
{p1_s3}
{p1_s4}
{p1_s5}
{p1_s6}
{p1_s7}
{p1_s8}

<!-- ═══════════════════ PART 2 ═══════════════════ -->
{part_divider(2, "Worker Setup")}
<p style="color:var(--ink-3);font-size:13.5px;margin-top:12px;">Run these steps on every laptop that will join the cluster as a worker. The master must already be running (Part 1 complete) before you start here.</p>

{p2_s1}
{p2_s2}
{p2_s3}
{p2_s4}
{p2_s5}

<!-- ═══════════════════ PART 3 ═══════════════════ -->
{part_divider(3, "Portability Test")}
<p style="color:var(--ink-3);font-size:13.5px;margin-top:12px;">These instructions are for the group that is <strong>testing Group 03's output</strong>. Follow them from any machine on the same LAN as the Group 03 master.</p>

{p3_intro}
{p3_s1}
{p3_s2}
{p3_s3}
{p3_s4}

</div><!-- /content -->

<footer>Group 03 &mdash; FIT3143 Parallel Computing &mdash; {today}</footer>
</main>

</div><!-- /layout -->

<script>
// ── OS Tab persistence ──────────────────────────────────────────────────────
const OS_KEY = 'preferred-os';

function activateOS(os) {{
  document.querySelectorAll('.os-tab').forEach(t => {{
    t.classList.toggle('active', t.dataset.os === os);
  }});
  document.querySelectorAll('.os-pane').forEach(p => {{
    p.classList.toggle('active', p.dataset.os === os);
  }});
  try {{ localStorage.setItem(OS_KEY, os); }} catch(e) {{}}
}}

function initTabs() {{
  const saved = (() => {{ try {{ return localStorage.getItem(OS_KEY); }} catch(e) {{ return null; }} }})();
  activateOS(saved || 'macos');
  document.querySelectorAll('.os-tab').forEach(tab => {{
    tab.addEventListener('click', () => activateOS(tab.dataset.os));
  }});
}}

// ── Copy buttons ────────────────────────────────────────────────────────────
function initCopyButtons() {{
  document.querySelectorAll('.copy-btn').forEach(btn => {{
    btn.addEventListener('click', async () => {{
      const code = btn.nextElementSibling.querySelector('code');
      const text = code ? code.innerText : '';
      try {{
        await navigator.clipboard.writeText(text);
        btn.textContent = '✓ Copied';
        btn.classList.add('copied');
        setTimeout(() => {{
          btn.textContent = 'Copy';
          btn.classList.remove('copied');
        }}, 2000);
      }} catch(err) {{
        // Fallback for non-HTTPS
        const ta = document.createElement('textarea');
        ta.value = text;
        ta.style.position = 'fixed';
        ta.style.opacity = '0';
        document.body.appendChild(ta);
        ta.select();
        document.execCommand('copy');
        document.body.removeChild(ta);
        btn.textContent = '✓ Copied';
        btn.classList.add('copied');
        setTimeout(() => {{ btn.textContent = 'Copy'; btn.classList.remove('copied'); }}, 2000);
      }}
    }});
  }});
}}

// ── Sidebar scroll spy ──────────────────────────────────────────────────────
function initScrollSpy() {{
  const links = Array.from(document.querySelectorAll('.toc-link'));
  const targets = links.map(l => document.querySelector(l.getAttribute('href'))).filter(Boolean);

  const observer = new IntersectionObserver(entries => {{
    entries.forEach(entry => {{
      if (entry.isIntersecting) {{
        const id = entry.target.id;
        links.forEach(l => l.classList.toggle('active', l.getAttribute('href') === '#' + id));
      }}
    }});
  }}, {{ rootMargin: '-10% 0px -80% 0px', threshold: 0 }});

  targets.forEach(t => observer.observe(t));
}}

// ── Hamburger ────────────────────────────────────────────────────────────────
function initHamburger() {{
  const btn = document.getElementById('hamburger');
  const sidebar = document.getElementById('sidebar');
  btn.addEventListener('click', () => {{
    const open = sidebar.classList.toggle('open');
    btn.classList.toggle('open', open);
  }});
  // Close on link click (mobile)
  sidebar.querySelectorAll('.toc-link').forEach(l => {{
    l.addEventListener('click', () => {{
      sidebar.classList.remove('open');
      btn.classList.remove('open');
    }});
  }});
  // Close on outside click
  document.addEventListener('click', e => {{
    if (!sidebar.contains(e.target) && !btn.contains(e.target)) {{
      sidebar.classList.remove('open');
      btn.classList.remove('open');
    }}
  }});
}}

// ── Boot ─────────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {{
  initTabs();
  initCopyButtons();
  initScrollSpy();
  initHamburger();
}});
</script>
</body>
</html>"""

out = DOCS_DIR / "manual.html"
out.write_text(HTML, encoding="utf-8")

print(f"✓ Manual generated: {out}")
print(f"  Size: {out.stat().st_size / 1024:.1f} KB")
print(f'  Preview: python3 -m http.server 8888 --directory docs')
print(f"  Open:    http://localhost:8888/manual.html")

#!/usr/bin/env python3
"""
generate_docs.py — Generates docs/index.html from structured content.
Run: python3 docs/generate_docs.py
"""

import os
from pathlib import Path

# ── Content ───────────────────────────────────────────────────────────────────

NAV = [
    {"part": "Part 0 — Prerequisites", "links": [
        ("0.1 Install Python", "#s0-1"),
        ("0.2 Install Java", "#s0-2"),
        ("0.3 Install Git", "#s0-3"),
        ("0.4 Enable SSH", "#s0-4"),
    ]},
    {"part": "Part 1 — Master Setup", "links": [
        ("1.1 Find Your LAN IP", "#s1-1"),
        ("1.2 Configure", "#s1-2"),
        ("1.3 Run Master Setup", "#s1-3"),
        ("1.4 Verify in Browser", "#s1-4"),
        ("1.5 Load the Dataset", "#s1-5"),
        ("1.6 Run PageRank", "#s1-6"),
        ("1.7 Start the API", "#s1-7"),
    ]},
    {"part": "Part 2 — Worker Setup", "links": [
        ("2.1 Before You Start", "#s2-1"),
        ("2.2 Clone and Configure", "#s2-2"),
        ("2.3 Run Worker Setup", "#s2-3"),
        ("2.4 Register with Master", "#s2-4"),
        ("2.5 Common Failures", "#s2-5"),
    ]},
    {"part": "Part 3 — Portability Test", "links": [
        ("3.1 Check Service is Up", "#s3-1"),
        ("3.2 Query Top 5 Results", "#s3-2"),
        ("3.3 Query a Specific Node", "#s3-3"),
        ("3.4 Top N Nodes", "#s3-4"),
        ("3.5 Outgoing Edges (Neighbors)", "#s3-5"),
        ("3.6 Incoming Edges (Influencers)", "#s3-6"),
        ("3.7 Job Statistics", "#s3-7"),
        ("3.8 Background Rerun", "#s3-8"),
        ("3.9 If Something Fails", "#s3-9"),
    ]},
]

SECTIONS = [

    # ═══════════════════════════════════════════════════════════
    # PART 0 — Prerequisites
    # ═══════════════════════════════════════════════════════════

    {
        "id": "s0-1", "num": "0.1", "title": "Install Python 3",
        "content": """
        <p>The first prerequisite for all cluster nodes. Python runs the setup scripts and the PageRank job.</p>
        {os_tabs:[
            {mac:["brew install python3"]},
            {linux:["sudo apt-get update","sudo apt-get install -y python3 python3-pip"]},
            {windows:["# Using winget (comes with Windows 10/11)","winget install Python.Python.3.12","# Or download from: https://python.org"]}
        ]}
        {callout:ok|Verify Python|Run <code>python3 --version</code> — should show Python 3.8 or higher.}
        """
    },

    {
        "id": "s0-2", "num": "0.2", "title": "Install Java",
        "content": """
        <p>Spark and Hadoop run on the Java Virtual Machine. Install OpenJDK 11 or 17 — Java 8 and 21+ cause compatibility issues.</p>
        {os_tabs:[
            {mac:["brew install openjdk@17","","# Add Java to your PATH permanently:","echo 'export PATH=\"$(brew --prefix openjdk@17)/bin:$PATH\"' >> ~/.zprofile","export PATH=\"$(brew --prefix openjdk@17)/bin:$PATH\""]},
            {linux:["sudo apt-get update","sudo apt-get install -y openjdk-17-jdk","","# Set JAVA_HOME:","echo 'export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64' >> ~/.bashrc","export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64"]},
            {windows:["winget install EclipseAdoptium.Temurin.17.JDK --silent","","# After install, set JAVA_HOME in PowerShell:","$env:JAVA_HOME = \"C:\\Program Files\\Eclipse Adoptium\\jdk-17.0.11.9-hotspot\"","# Or download from: https://adoptium.net"]}
        ]}
        {callout:ok|Verify Java|Run <code>java -version</code> — should show <em>11</em> or <em>17</em>. Java 8 and Java 21+ cause problems.}
        """
    },

    {
        "id": "s0-3", "num": "0.3", "title": "Install Git",
        "content": """
        <p>Git is used to clone the cluster repository onto each machine.</p>
        {os_tabs:[
            {mac:["brew install git"]},
            {linux:["sudo apt-get update","sudo apt-get install -y git"]},
            {windows:["winget install Git.Git --silent","# Or download from: https://git-scm.com"]}
        ]}
        {callout:ok|Verify Git|Run <code>git --version</code> — should show <em>2.x.x</em>.}
        """
    },

    {
        "id": "s0-4", "num": "0.4", "title": "Enable SSH",
        "content": """
        <p>Hadoop daemons communicate between nodes using SSH. Enable Remote Login on your machine:</p>
        {os_tabs:[
            {mac:["# Option 1: GUI — System Settings → General → Remote Login → ON","","# Option 2: Command line (requires admin password):","sudo systemsetup -setremotelogin on","","# Verify:","sudo systemsetup -getremotelogin"]},
            {linux:["# Most Linux distros have SSH pre-installed. Verify it's running:","which ssh","sudo systemctl enable ssh","sudo systemctl start ssh"]},
            {windows:["# Windows 10/11 has OpenSSH client built-in. Verify:","Get-WindowsCapability -Online | Where-Object Name -like 'OpenSSH*'","","# If needed, install via Settings → Apps → Optional Features → Add OpenSSH Client"]}
        ]}
        {callout:warn|SSH is required|Hadoop's start scripts use SSH to communicate between nodes. Without SSH enabled, the cluster will fail to start. This is a common issue on fresh macOS machines — macOS does not enable it by default.}
        """
    },

    # ═══════════════════════════════════════════════════════════
    # PART 1 — Master Setup
    # ═══════════════════════════════════════════════════════════

    {
        "id": "s1-1", "num": "1.1", "title": "Find Your LAN IP",
        "content": """
        <p>Your LAN IP is the address other machines on the same Wi-Fi will use to reach yours. It usually starts with <code>192.168.</code> or <code>10.</code>.</p>
        {os_tabs:[
            {mac:["ipconfig getifaddr en0","# Expected output example:","# 192.168.1.14"]},
            {linux:["hostname -I | awk '{print $1}'","# Expected output example:","# 192.168.1.14"]},
            {windows:["(Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.IPAddress -like '192.168.*' }).IPAddress","# Expected output example:","# 192.168.1.14"]}
        ]}
        {callout:tip|Can't find your IP?|Make sure your machine is connected to the same Wi-Fi as the other nodes. Ethernet connections may show up on <code>en1</code> (macOS) or <code>eth0</code> (Linux) instead.}
        """
    },

    {
        "id": "s1-2", "num": "1.2", "title": "Configure",
        "content": """
        <p>Open <code>setup/config.py</code>. There is exactly one line you need to change — <code>MASTER_IP</code>. Everything else is auto-detected.</p>
        <p><strong>Before</strong> (the default placeholder):</p>
        {code:python|Master_IP = "192.168.1.14"   # set to master laptop's LAN IP}
        <p><strong>After</strong> (your actual LAN IP from Section 1.1):</p>
        {code:python|MASTER_IP = "192.168.1.42"   # your actual LAN IP here}
        {callout:warn|Set this before running anything|Every setup script imports <code>config.py</code>. If <code>MASTER_IP</code> is wrong, Hadoop and Spark will start but workers will be unable to connect — and the error messages won't point here.}
        <p>Verify the config loads cleanly:</p>
        {code:bash|python3 setup/config.py}
        {callout:ok|Expected output|<pre>OS          : Darwin
Local IP    : 192.168.1.42
MASTER_IP   : 192.168.1.42
JAVA_HOME   : /opt/homebrew/opt/openjdk@17
HADOOP_HOME : /opt/hadoop-3.3.6
SPARK_HOME  : /opt/spark-3.5.3-bin-hadoop3
  [ok] Java: openjdk version "17.0.11" 2024-01-16</pre>}
        """
    },

    {
        "id": "s1-3", "num": "1.3", "title": "Run Master Setup",
        "content": """
        <p>This single command installs Hadoop (a distributed filesystem) and Spark (a distributed computation engine), formats the filesystem, and starts all required services.</p>
        {code:bash|python3 setup/setup_node.py --role master}
        <p>The script prints phases as it runs. Here is what each one means:</p>
        {table:[
            ["Phase printed", "What is happening"],
            ["<code>-- Java --</code>", "Checks Java is present; installs if missing."],
            ["<code>-- Python dependencies --</code>", "Installs <code>pyspark</code>, <code>flask</code>, <code>requests</code> via pip."],
            ["<code>-- Hadoop 3.3.6 (master) --</code>", "Downloads ~650 MB Hadoop archive and extracts it. Writes XML config files pointing at your <code>MASTER_IP</code>."],
            ["<code>-- Spark 3.5.3 (master) --</code>", "Downloads ~300 MB Spark archive and extracts it. Writes <code>spark-defaults.conf</code>."],
            ["<code>-- Formatting NameNode --</code>", "Initialises the HDFS metadata directory. Only happens once; skipped on re-runs."],
            ["<code>-- Starting services (master) --</code>", "Launches NameNode, DataNode, SecondaryNameNode, and Spark Master as background daemons."],
            ["<code>-- Verification --</code>", "Runs <code>jps</code> to list running Java processes and confirms all four are present."],
        ]}
        {callout:tip|This takes a while the first time|Downloading Hadoop + Spark is about 1 GB total. On a fast connection expect 3-5 minutes; on a slow one, up to 20. Subsequent runs skip the download.}
        <h4>After it finishes: check with <code>jps</code></h4>
        <p><code>jps</code> — the Java Virtual Machine Process Status tool — lists every running Java process. After master setup you should see exactly four:</p>
        {code:bash|jps}
        {callout:ok|Expected output — all four must appear|<pre>12345 NameNode
12346 DataNode
12347 SecondaryNameNode
12348 Master
12349 Jps</pre>}
        <p>If a process is missing, here is where to look:</p>
        {table:[
            ["Missing process", "What to check"],
            ["<code>NameNode</code>", "Check Hadoop logs in <code>$HADOOP_HOME/logs/</code>. Common cause: a NameNode is already running (stop it with <code>stop-dfs.sh</code>), or wrong <code>JAVA_HOME</code> in <code>hadoop-env.sh</code>."],
            ["<code>DataNode</code>", "Usually starts after NameNode. If NameNode is up but DataNode isn't, check for port 9000 conflicts: <code>lsof -i :9000</code>."],
            ["<code>SecondaryNameNode</code>", "Non-critical for this lab. Its absence won't block PageRank."],
            ["<code>Master</code> (Spark)", "Check Spark logs in <code>$SPARK_HOME/logs/</code>."],
        ]}
        """
    },

    {
        "id": "s1-4", "num": "1.4", "title": "Verify in Browser",
        "content": """
        <p>Two web UIs start automatically. Open them to confirm the cluster is healthy.</p>
        <h4>Spark UI — <code>http://192.168.1.14:8080</code></h4>
        <p>You should see the Spark Master dashboard. Look for: <strong>Status: ALIVE</strong> and at least one worker listed under "Workers" (the master itself counts as a worker at this stage).</p>
        <h4>HDFS NameNode UI — <code>http://192.168.1.14:9870</code></h4>
        <p>You should see the Hadoop NameNode overview. Look for: <strong>Live Nodes: 1</strong> (or more once workers join) and <strong>Safe Mode: OFF</strong>.</p>
        {callout:warn|If the browser just times out|The ports are blocked by a firewall. Open them:}
        {os_tabs:[
            {mac:["# macOS — allow Java through the firewall (or disable it temporarily):","sudo /usr/libexec/ApplicationFirewall/socketfilterfw --setglobalstate off","","# Linux — open the required ports:","sudo ufw allow 8080/tcp","sudo ufw allow 9870/tcp","sudo ufw allow 9000/tcp","sudo ufw allow 7077/tcp","sudo ufw allow 5000/tcp","","# Windows — open via PowerShell (as Administrator):","netsh advfirewall firewall add rule name=\"Hadoop Spark Cluster\" dir=in action=allow protocol=TCP localport=8080,9870,9000,7077,5000"]},
            {linux:["# macOS — allow Java through the firewall (or disable it temporarily):","sudo /usr/libexec/ApplicationFirewall/socketfilterfw --setglobalstate off","","# Linux — open the required ports:","sudo ufw allow 8080/tcp","sudo ufw allow 9870/tcp","sudo ufw allow 9000/tcp","sudo ufw allow 7077/tcp","sudo ufw allow 5000/tcp","","# Windows — open via PowerShell (as Administrator):","netsh advfirewall firewall add rule name=\"Hadoop Spark Cluster\" dir=in action=allow protocol=TCP localport=8080,9870,9000,7077,5000"]},
            {windows:["# macOS — allow Java through the firewall (or disable it temporarily):","sudo /usr/libexec/ApplicationFirewall/socketfilterfw --setglobalstate off","","# Linux — open the required ports:","sudo ufw allow 8080/tcp","sudo ufw allow 9870/tcp","sudo ufw allow 9000/tcp","sudo ufw allow 7077/tcp","sudo ufw allow 5000/tcp","","# Windows — open via PowerShell (as Administrator):","netsh advfirewall firewall add rule name=\"Hadoop Spark Cluster\" dir=in action=allow protocol=TCP localport=8080,9870,9000,7077,5000"]}
        ]}
        """
    },

    {
        "id": "s1-5", "num": "1.5", "title": "Load the Dataset",
        "content": """
        <p>The dataset is the Stanford Web-Google graph — a snapshot of 875,713 web pages and 5,105,039 hyperlinks between them, collected by Google in 2002. HDFS (the Hadoop Distributed File System) stores data across all nodes so Spark can read it in parallel.</p>
        <h4>Step 1 — Download</h4>
        {code:bash|python3 src/download_dataset.py}
        {callout:ok|Expected output|<pre>Downloading from https://snap.stanford.edu/data/web-Google.txt.gz ...
  [####################] 100%
Extracting...

[ok] Ready: data/web-Google.txt
  Nodes: 875,713
  Edges: 5,105,039

Next: hdfs dfs -put data/web-Google.txt /pagerank/input/</pre>}
        <h4>Step 2 — Push to HDFS</h4>
        <p><code>hdfs dfs -put</code> copies a local file into the distributed filesystem so all workers can access it.</p>
        {os_tabs:[
            {mac:["hdfs dfs -put data/web-Google.txt /pagerank/input/"]},
            {linux:["hdfs dfs -put data/web-Google.txt /pagerank/input/"]},
            {windows:["hdfs dfs -put data/web-Google.txt /pagerank/input/"]}
        ]}
        {callout:ok|Expected output|<p>No output means success. Verify the file landed:</p><pre>hdfs dfs -ls /pagerank/input/

-rw-r--r--   2 user supergroup  804298888 2024-05-09 /pagerank/input/web-Google.txt</pre>}
        {callout:tip|Already in HDFS?|If you re-run, use <code>hdfs dfs -put -f</code> (force overwrite) to replace an existing file.}
        """
    },

    {
        "id": "s1-6", "num": "1.6", "title": "Run PageRank",
        "content": """
        <p>This submits the PageRank job to Spark. <code>spark-submit</code> packages your Python script and sends it to the Spark Master, which distributes the computation across all connected workers.</p>
        {code:bash|spark-submit \\
  --master spark://192.168.1.14:7077 \\
  --executor-memory 2g \\
  --driver-memory 1g \\
  src/pagerank.py 10}
        <p>The number <code>10</code> is the iteration count. During the run you will see lines like:</p>
        {callout:ok|Iteration output|<pre>  Iteration  1/10  12.3s
  Iteration  2/10  11.8s
  Iteration  3/10  11.5s
  ...
  Iteration 10/10  11.2s

Collecting results...

=======================================================
  TOP 5 MOST INFLUENTIAL NODES
=======================================================
  #1  node      41909  ->  445.71778597
  #2  node     597621  ->  406.62836675
  #3  node     504140  ->  399.08930875
  #4  node     384666  ->  392.82584373
  #5  node     537039  ->  383.90912550
=======================================================

[ok] Done in 118.4s</pre>}
        <p>Each iteration line shows the wall-clock time for one pass over the graph. Times should be roughly stable; a sudden spike usually means a worker disconnected.</p>
        <h4>Where results are saved</h4>
        {table:[
            ["File", "Contents"],
            ["<code>data/top5.json</code>", "Top 5 nodes — this is what the API serves."],
            ["<code>data/results.json</code>", "Top 1000 nodes with scores, for <code>/node/&lt;id&gt;</code> and <code>/top/&lt;n&gt;</code> queries."],
            ["<code>data/graph.json</code>", "Full adjacency list — every node and its outgoing neighbors. Used by <code>/neighbors</code> and <code>/influencedby</code>."],
            ["<code>data/meta.json</code>", "Job metadata — dataset name, node/edge counts, iterations, damping factor, top node, completion timestamp. Used by <code>/stats</code>."],
            ["<code>data/pagerank_output/part-00000</code>", "All nodes, tab-separated: <code>nodeId\\tscreen</code>."],
        ]}
        """
    },

    {
        "id": "s1-7", "num": "1.7", "title": "Start the API",
        "content": """
        <p>The REST API is a small Flask server that reads <code>data/top5.json</code> and serves it to other groups over HTTP.</p>
        <h4>Verify locally first</h4>
        {code:bash|python3 src/api.py}
        {callout:ok|Expected startup output|<pre>==================================================
  Group 03 - PageRank Portability API
  http://192.168.1.14:5000

  GET  /top5              -> top 5 influencers
  GET  /top/&lt;n&gt;          -> top N ranked nodes
  GET  /node/&lt;id&gt;         -> score for node id
  GET  /neighbors/&lt;id&gt;    -> outgoing edges
  GET  /influencedby/&lt;id&gt; -> incoming edges
  GET  /stats             -> job metadata + service info
  POST /rerun             -> trigger background rerun
  GET  /rerun/status      -> rerun job status
  GET  /health            -> status check

  [ok] Results loaded -- top node: 41909 (445.71778597)
==================================================</pre>}
        <p>In a second terminal, confirm it responds:</p>
        {code:bash|curl http://localhost:5000/health}
        <h4>Run it in the background (so you can close the terminal)</h4>
        {os_tabs:[
            {mac:["nohup python3 src/api.py > /tmp/api.log 2>&1 &","echo \"API PID: $!\"","# To stop it later:","# kill $(lsof -ti :5000)"]},
            {linux:["nohup python3 src/api.py > /tmp/api.log 2>&1 &","echo \"API PID: $!\"","# To stop it later:","# kill $(lsof -ti :5000)"]},
            {windows:["# PowerShell -- start as a background job","Start-Job -ScriptBlock { python3 src/api.py } | Out-Null","Write-Host 'API started in background'","# To stop: Get-Job | Stop-Job"]}
        ]}
        <h4>Three ways to verify it works</h4>
        {code:bash|# Option 1 -- curl
curl http://localhost:5000/health

# Option 2 -- Python (works on all three OS)
python3 -c "import urllib.request, json; print(json.loads(urllib.request.urlopen('http://localhost:5000/health').read()))"

# Option 3 -- Browser
# Open: http://localhost:5000/health}
        {callout:tip|macOS port 5000 conflict|macOS Monterey+ reserves port 5000 for AirPlay Receiver. If <code>curl</code> returns <em>connection refused</em>, go to <strong>System Settings → AirDrop &amp; Handoff</strong> and turn off AirPlay Receiver. Then restart the API.}
        """
    },

    # ═══════════════════════════════════════════════════════════
    # PART 2 — Worker Setup
    # ═══════════════════════════════════════════════════════════

    {
        "id": "s2-1", "num": "2.1", "title": "Before You Start",
        "content": """
        <p>The master node must be fully running before you set up any worker. Specifically:</p>
        <ul>
          <li>Section 1.3 must be complete — <code>jps</code> on the master shows all four processes.</li>
          <li>You need the master's LAN IP address from Section 1.1.</li>
          <li>Both machines must be on the same Wi-Fi or wired LAN.</li>
        </ul>
        {os_tabs:[
            {mac:["ping -c 3 192.168.1.14","# All 3 packets should receive a reply."]},
            {linux:["ping -c 3 192.168.1.14","# All 3 packets should receive a reply."]},
            {windows:["ping -n 3 192.168.1.14","# All 3 packets should receive a reply."]}
        ]}
        {callout:warn|Different Wi-Fi networks|University campuses often have network isolation between clients on the same SSID. If ping fails even though you're on the same network, use a personal hotspot or a wired switch shared between the machines.}
        """
    },

    {
        "id": "s2-2", "num": "2.2", "title": "Clone and Configure",
        "content": """
        <h4>Clone the repository on the worker machine</h4>
        {os_tabs:[
            {mac:["git clone https://github.com/munimx/pagerank-cluster","cd pagerank-cluster"]},
            {linux:["git clone https://github.com/munimx/pagerank-cluster","cd pagerank-cluster"]},
            {windows:["git clone https://github.com/munimx/pagerank-cluster","cd pagerank-cluster"]}
        ]}
        <h4>Set <code>MASTER_IP</code> in <code>setup/config.py</code></h4>
        <p>Open the file and change the one line:</p>
        {code:python|MASTER_IP = "192.168.1.42"   # the MASTER's LAN IP, NOT your own}
        {callout:warn|Common mistake — setting MASTER_IP to your own IP on a worker machine|On the <strong>worker</strong>, <code>MASTER_IP</code> must be the IP of the <strong>master laptop</strong>, not the worker's own IP. If you set it to your own IP, the worker will try to connect to itself as a master — and fail silently. Double-check before running setup.}
        """
    },

    {
        "id": "s2-3", "num": "2.3", "title": "Run Worker Setup",
        "content": """
        {code:bash|python3 setup/setup_node.py --role worker}
        <p>This installs Java, Python dependencies, Hadoop, and Spark — same as the master, but starts only the DataNode and Spark Worker daemons (not the NameNode or Spark Master).</p>
        <h4>After it finishes: check with <code>jps</code></h4>
        {code:bash|jps}
        {callout:ok|Expected output on the worker — exactly these two|<pre>23456 DataNode
23457 Worker
23458 Jps</pre>
        <p>You should <strong>not</strong> see <code>NameNode</code> or <code>Master</code> on a worker — those only run on the master machine.</p>}
        """
    },

    {
        "id": "s2-4", "num": "2.4", "title": "Register with Master",
        "content": """
        <p>The master needs to know this worker exists. This is a two-step handshake: the worker reports its IP, then the master adds it to the cluster roster.</p>
        <h4>Step 1 — Find your own IP (on the worker machine)</h4>
        {os_tabs:[
            {mac:["ipconfig getifaddr en0"]},
            {linux:["hostname -I | awk '{print $1}'"]},
            {windows:["(Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.IPAddress -like '192.168.*' }).IPAddress"]}
        ]}
        <h4>Step 2 — Send your IP to the master operator</h4>
        <p>Tell the person running the master laptop your IP (e.g., via Slack, Discord, or just say it out loud). They run this on the master:</p>
        {code:bash|# On the MASTER machine -- replace with the worker's actual IP
python3 setup/register_worker.py 192.168.1.55}
        {os_tabs:[
            {mac:["python3 setup/register_worker.py 192.168.1.55"]},
            {linux:["python3 setup/register_worker.py 192.168.1.55"]},
            {windows:["python setup/register_worker.py 192.168.1.55"]}
        ]}
        <h4>Step 3 — Verify from the master</h4>
        {code:bash|hdfs dfsadmin -report | grep 'Live datanodes'}
        {os_tabs:[
            {mac:["hdfs dfsadmin -report | grep 'Live datanodes'"]},
            {linux:["hdfs dfsadmin -report | grep 'Live datanodes'"]},
            {windows:["hdfs dfsadmin -report | findstr \"Live datanodes\""]}
        ]}
        {callout:ok|Expected output|<p><code>Live datanodes (2):</code> — the count increases by 1 each time a worker is registered. If you have 1 worker plus the master's own DataNode, you'll see 2.</p>}
        """
    },

    {
        "id": "s2-5", "num": "2.5", "title": "Most Common Failures",
        "content": """
        <h4>Failure 1 — <code>MASTER_IP</code> mismatch</h4>
        <p>The worker starts but never appears in the Spark UI or HDFS report.</p>
        {callout:ok|What the error looks like in Spark Worker logs|<pre>ERROR Worker: All masters are unresponsive! Giving up.
ERROR Worker: Connection to spark://192.168.1.99:7077 failed</pre>}
        <p><strong>Fix:</strong> Open <code>setup/config.py</code> on the <em>worker</em> machine and correct <code>MASTER_IP</code> to the master's actual LAN IP. Then re-run worker setup.</p>
        <h4>Failure 2 — Worker can't reach master (firewall)</h4>
        <p>Ping succeeds but Spark/HDFS connections time out.</p>
        {os_tabs:[
            {mac:["# Option 1: Disable the firewall (simplest for a lab cluster):","sudo /usr/libexec/ApplicationFirewall/socketfilterfw --setglobalstate off","","# Option 2: Allow Java through the firewall:","sudo /usr/libexec/ApplicationFirewall/socketfilterfw --add /usr/bin/java"]},
            {linux:["sudo ufw allow 7077/tcp","sudo ufw allow 9000/tcp","sudo ufw allow 9866/tcp","sudo ufw allow 9867/tcp","sudo ufw allow 8080/tcp","sudo ufw allow 9870/tcp"]},
            {windows:["# Run as Administrator:","netsh advfirewall firewall add rule name=\"Hadoop-Spark Cluster\" dir=in action=allow protocol=TCP localport=7077,9000,9866,9867,8080,9870"]}
        ]}
        """
    },

    # ═══════════════════════════════════════════════════════════
    # PART 3 — Portability Test
    # ═══════════════════════════════════════════════════════════

    {
        "id": "s3-1", "num": "3.1", "title": "Check the Service Is Up",
        "content": """
        <p>Before querying results, confirm the API process is alive.</p>
        <h4>Three ways to call <code>GET /health</code></h4>
        {code:bash|# curl
curl http://192.168.1.14:5000/health

# Python
python3 -c "import urllib.request, json; print(json.dumps(json.loads(urllib.request.urlopen('http://192.168.1.14:5000/health').read()), indent=2))"

# Browser
# http://192.168.1.14:5000/health}
        {callout:ok|Healthy response|<pre>{
  "dataset": "Stanford Web-Google",
  "framework": "Apache Spark",
  "group": "03",
  "results_ready": true,
  "status": "ok",
  "task": "Network Graph PageRank"
}</pre>}
        {callout:warn|Failed / unexpected response|<p>If the connection is refused: the API process isn't running. Contact the Group 03 master operator to restart it (<code>python3 src/api.py &amp;</code>).</p>
        <p>If you get a timeout: check network connectivity with <code>ping</code> first, then check firewall rules (Section 2.5).</p>}
        """
    },

    {
        "id": "s3-2", "num": "3.2", "title": "Query the Top 5 Results",
        "content": """
        <p><code>GET /top5</code> returns the five highest-ranked nodes in the Web-Google graph.</p>
        {code:bash|# curl
curl http://192.168.1.14:5000/top5

# Python urllib (no extra libraries needed)
python3 -c "
import urllib.request, json
data = json.loads(urllib.request.urlopen('http://192.168.1.14:5000/top5').read())
for n in data:
    print(n['rank'], n['nodeId'], n['pagerank'])
"

# Browser
# http://192.168.1.14:5000/top5}
        {callout:ok|Expected JSON response|<pre>[
  {
    "rank": 1,
    "nodeId": "41909",
    "pagerank": 445.71778597
  },
  {
    "rank": 2,
    "nodeId": "597621",
    "pagerank": 406.62836675
  },
  {
    "rank": 3,
    "nodeId": "504140",
    "pagerank": 399.08930875
  },
  {
    "rank": 4,
    "nodeId": "384666",
    "pagerank": 392.82584373
  },
  {
    "rank": 5,
    "nodeId": "537039",
    "pagerank": 383.9091255
  }
]</pre>}
        {callout:tip|Scores may differ slightly|PageRank scores depend on the number of iterations and the damping factor. Our run used 10 iterations and damping 0.85. Node IDs will match; the exact floating-point values may vary by &plusmn;0.001 if you re-run with different settings.}
        """
    },

    {
        "id": "s3-3", "num": "3.3", "title": "Query a Specific Node",
        "content": """
        <p><code>GET /node/&lt;id&gt;</code> returns the score for one node. Use the top-ranked node's ID as your test case.</p>
        {code:bash|# curl -- query the top node
curl http://192.168.1.14:5000/node/41909

# Python
python3 -c "
import urllib.request, json
data = json.loads(urllib.request.urlopen('http://192.168.1.14:5000/node/41909').read())
print(json.dumps(data, indent=2))
"}
        {callout:ok|Expected response|<pre>{
  "nodeId": "41909",
  "pagerank": 445.71778597
}</pre>}
        """
    },

    {
        "id": "s3-4", "num": "3.4", "title": "Top N Nodes",
        "content": """
        <p><code>GET /top/&lt;n&gt;</code> returns the top <em>n</em> ranked nodes (capped at 1000, the size of the stored result set).</p>
        {code:bash|# Get top 10 nodes
curl http://192.168.1.14:5000/top/10

# Get top 50 nodes
curl http://192.168.1.14:5000/top/50}
        {callout:ok|Response format|<pre>{
  "requested": 10,
  "returned": 10,
  "nodes": [
    {"nodeId": "41909", "pagerank": 445.71778597},
    {"nodeId": "597621", "pagerank": 406.62836675},
    ...
  ]
}</pre>}
        <h4>Edge cases</h4>
        <ul>
          <li><code>n &lt; 1</code> &rarr; returns <code>400</code> with error message.</li>
          <li><code>n &gt; 1000</code> &rarr; returns all 1000 available nodes with a <code>note</code> field explaining the cap.</li>
        </ul>
        """
    },

    {
        "id": "s3-5", "num": "3.5", "title": "Outgoing Edges (Neighbors)",
        "content": """
        <p><code>GET /neighbors/&lt;node_id&gt;</code> returns every node that the given node links <em>to</em> (outgoing edges, i.e. the node's adjacency list).</p>
        {code:bash|# Get all outgoing neighbors of the top-ranked node
curl http://192.168.1.14:5000/neighbors/41909

# Python
python3 -c "
import urllib.request, json
data = json.loads(urllib.request.urlopen('http://192.168.1.14:5000/neighbors/41909').read())
print(json.dumps(data, indent=2))
"}
        {callout:ok|Response format|<pre>{
  "nodeId": "41909",
  "direction": "outgoing",
  "count": 42,
  "neighbors": ["123", "456", "789", ...]
}</pre>}
        <h4>Sink nodes</h4>
        <p>Nodes with no outgoing edges (sink nodes) will return <code>404</code> with the message: <em>This may be a sink node (has no outgoing edges — it receives links but doesn't link to anything).</em> This is expected behaviour — sink nodes exist in the graph but have no entries in the adjacency list.</p>
        """
    },

    {
        "id": "s3-6", "num": "3.6", "title": "Incoming Edges (Influencers)",
        "content": """
        <p><code>GET /influencedby/&lt;node_id&gt;</code> returns every node that links <em>to</em> the given node (incoming edges). This is computed on first request by building a reverse-index from <code>data/graph.json</code>, then cached in memory for all subsequent calls — it does not rebuild on every request.</p>
        {code:bash|# Get all nodes that link to the top-ranked node
curl http://192.168.1.14:5000/influencedby/41909

# Python
python3 -c "
import urllib.request, json
data = json.loads(urllib.request.urlopen('http://192.168.1.14:5000/influencedby/41909').read())
print(f\"Node {data['nodeId']} is influenced by {data['count']} nodes\")
"}
        {callout:ok|Response format|<pre>{
  "nodeId": "41909",
  "direction": "incoming",
  "count": 18,
  "sources": ["789", "101", "202", ...]
}</pre>}
        """
    },

    {
        "id": "s3-7", "num": "3.7", "title": "Job Statistics",
        "content": """
        <p><code>GET /stats</code> returns the job metadata recorded when <code>pagerank.py</code> finished, plus live service information.</p>
        {code:bash|curl http://192.168.1.14:5000/stats

# Python
python3 -c "
import urllib.request, json
print(json.dumps(json.loads(urllib.request.urlopen('http://192.168.1.14:5000/stats').read()), indent=2))
"}
        {callout:ok|Response format|<pre>{
  "dataset": "web-Google.txt",
  "total_nodes": 875713,
  "total_edges": 5105039,
  "iterations": 10,
  "damping_factor": 0.85,
  "top_node": "41909",
  "completed_at": "2026-05-10T12:34:56+00:00",
  "api_status": "ok",
  "endpoints": ["/top5", "/top/<n>", "/node/<id>", "/neighbors/<id>", "/influencedby/<id>", "/stats", "/rerun", "/health"]
}</pre>}
        """
    },

    {
        "id": "s3-8", "num": "3.8", "title": "Background Rerun",
        "content": """
        <p><code>POST /rerun</code> triggers a PageRank rerun in the background. It accepts optional parameters to change the iteration count, damping factor, or swap to an entirely different dataset from SNAP.</p>
        {code:bash|# Rerun with more iterations
curl -X POST http://192.168.1.14:5000/rerun \\
  -H 'Content-Type: application/json' \\
  -d '{"iterations": 15}'

# Rerun with different damping factor
curl -X POST http://192.168.1.14:5000/rerun \\
  -H 'Content-Type: application/json' \\
  -d '{"damping_factor": 0.90}'

# Swap dataset entirely — Twitter graph from SNAP
curl -X POST http://192.168.1.14:5000/rerun \\
  -H 'Content-Type: application/json' \\
  -d '{"dataset_url": "https://snap.stanford.edu/data/twitter_combined.txt.gz"}'

# Combine all parameters
curl -X POST http://192.168.1.14:5000/rerun \\
  -H 'Content-Type: application/json' \\
  -d '{"iterations": 20, "damping_factor": 0.88, "dataset_url": "https://snap.stanford.edu/data/web-Google.txt.gz"}'}
        {callout:ok|Immediate response (202 Accepted)|<pre>{
  "job_id": "rerun_1746861234",
  "status": "queued",
  "params": {"iterations": 15}
}</pre>}
        <h4>Check job status</h4>
        {code:bash|curl http://192.168.1.14:5000/rerun/status}
        {callout:ok|Status responses|<pre>// idle (no rerun ever triggered)
{"status": "idle"}

// running
{"status": "running", "job_id": "rerun_1746861234", "started_at": "2026-05-10T12:00:00+00:00", ...}

// completed
{"status": "completed", "job_id": "rerun_1746861234", "completed_at": "2026-05-10T12:02:45+00:00", ...}

// failed
{"status": "failed", "job_id": "rerun_1746861234", "error": "..."}</pre>}
        {callout:warn|Dataset swap requires a SNAP URL|When <code>dataset_url</code> is provided, the API downloads the file, places it in HDFS, updates the metadata, then runs <code>pagerank.py</code>. The URL must point to a gzipped SNAP graph file (e.g. from <code>https://snap.stanford.edu/data/</code>). The file is downloaded locally, extracted, then pushed to HDFS so it is available to all cluster nodes.}
        {callout:tip|The API stays responsive during a rerun|The rerun happens in a background thread. The API continues to serve requests using the <em>previous</em> results until the new job completes. When the job finishes, the API updates all result files and future queries return the new results. The reverse-index cache is also invalidated so <code>/influencedby</code> reflects the new graph.}
        """
    },

    {
        "id": "s3-9", "num": "3.9", "title": "If Something Fails",
        "content": """
        <h4>API unreachable (connection refused / timeout)</h4>
        <p>Step 1: confirm basic network connectivity first.</p>
        {code:bash|ping -c 4 192.168.1.14}
        {os_tabs:[
            {mac:["ping -c 4 192.168.1.14"]},
            {linux:["ping -c 4 192.168.1.14"]},
            {windows:["ping -n 4 192.168.1.14"]}
        ]}
        <p>If ping fails, you are on different networks. If ping succeeds but the API is still unreachable, the firewall is blocking port 5000. Apply the firewall rules from Section 2.5 on the <strong>master</strong> machine.</p>
        <h4>503 response — results not ready</h4>
        {callout:ok|503 response body|<pre>{"error": "Results not ready. Run src/pagerank.py first."}</pre>
        <p>The PageRank job has not finished yet (or has not been run at all). Contact the Group 03 master operator. Do not mark the portability test as failed immediately — the job takes approximately 2 minutes to complete.</p>}
        <h4>404 on a node ID</h4>
        {callout:ok|404 response body|<pre>{"error": "Node '999999' not in top-1000 results."}</pre>
        <p>The API only stores the top 1000 nodes by PageRank score. A 404 for a node ID that is not in the top 1000 is expected and correct behaviour — it does not indicate a bug.</p>}
        """
    },
]

# ── HTML Generator ─────────────────────────────────────────────────────────────

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

JAVASCRIPT = """
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
      btn.textContent = '\\u2713 Copied';
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


def esc(s):
    return (str(s)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;"))


def render_code_block(lang, lines):
    code = "\n".join(esc(line) for line in lines)
    return f'''<div class="code-wrap"><button class="copy-btn" aria-label="Copy code">Copy</button><pre><code class="lang-{lang}">{code}</code></pre></div>'''


def render_os_tabs(tabs_data):
    """tabs_data is a dict: {mac: [...], linux: [...], windows: [...]}"""
    panes = []
    for os_name in ("macos", "linux", "windows"):
        key = "mac" if os_name == "macos" else os_name
        lines = tabs_data.get(key, [])
        if lines:
            code = "\n".join(esc(line) for line in lines)
            panes.append(f'''<div class="os-pane" data-os="{os_name}"><div class="code-wrap"><button class="copy-btn" aria-label="Copy code">Copy</button><pre><code class="lang-bash">{code}</code></pre></div></div>''')

    tabs_html = "".join(
        f'''<button class="os-tab" role="tab" data-os="{os}">{"macOS" if os == "macos" else os.capitalize()}</button>'''
        for os in ("macos", "linux", "windows")
        if tabs_data.get("mac" if os == "macos" else os)
    )

    return f'''<div class="os-tabs"><div class="os-tab-bar" role="tablist">{tabs_html}</div>{"".join(panes)}</div>'''


def render_table(rows):
    header = rows[0]
    body = rows[1:]
    th = "".join(f"<th>{esc(cell)}</th>" for cell in header)
    trs = "".join(
        f"<tr>{''.join(f'<td>{cell}</td>' for cell in row)}</tr>"
        for row in body
    )
    return f'''<table><thead><tr>{th}</tr></thead><tbody>{trs}</tbody></table>'''


def render_callout(type_, title, body_html):
    icons = {"warn": "&#9888;", "ok": "&#10003;", "tip": "&#128161;"}
    return f'''<div class="callout callout-{type_}"><span class="callout-icon">{icons[type_]}</span><div><strong>{esc(title)}</strong>{body_html}</div></div>'''


def parse_content(template):
    """Convert template tokens to HTML."""
    html_parts = []
    i = 0
    while i < len(template):
        # Check for {os_tabs:...}
        start = template.find("{os_tabs:[", i)
        # Check for {code:...}
        start2 = template.find("{code:", i)
        # Check for {table:[...]}
        start3 = template.find("{table:[", i)
        # Check for {callout:...}
        start4 = template.find("{callout:", i)

        candidates = [x for x in [start, start2, start3, start4] if x != -1]
        if not candidates:
            html_parts.append(template[i:])
            break

        earliest = min(candidates)

        html_parts.append(template[i:earliest])
        i = earliest

        if start == earliest:
            # Find matching ]}
            depth = 0
            j = start + 9
            start_content = j
            while j < len(template):
                if template[j] == '[':
                    depth += 1
                elif template[j] == ']':
                    if depth == 0:
                        break
                    depth -= 1
                j += 1

            content = template[start_content:j]
            i = j + 2  # skip ]}

            # Parse {mac:[...]} {linux:[...]} {windows:[...]} blocks
            import re
            tabs_data = {"mac": [], "linux": [], "windows": []}
            # Match each {key:[...]} by finding the matching ] for each [
            pos = 0
            while pos < len(content):
                brace = content.find("{", pos)
                if brace == -1:
                    break
                colon = content.find(":", brace)
                bracket = content.find("[", colon)
                if colon == -1 or bracket == -1:
                    pos = brace + 1
                    continue
                key = content[brace + 1:colon]
                if key not in tabs_data:
                    pos = brace + 1
                    continue
                # Find matching ] for the [ at bracket
                depth = 0
                end = bracket
                while end < len(content):
                    if content[end] == "[":
                        depth += 1
                    elif content[end] == "]":
                        depth -= 1
                        if depth == 0:
                            break
                    end += 1
                inner = content[bracket + 1:end]
                # Split by comma, strip quotes
                lines = []
                for part in inner.split(","):
                    s = part.strip().strip('"')
                    if s:
                        lines.append(s)
                tabs_data[key] = lines
                pos = end + 1

            html_parts.append(render_os_tabs(tabs_data))
            i = j + 2  # advance past ]}

        elif start2 == earliest:
            end = template.find("}", i + 6)
            inner = template[i + 6:end]
            i = end + 1

            if "|" in inner:
                lang, code = inner.split("|", 1)
                code = code.strip()
                lines = code.split("\n")
                html_parts.append(render_code_block(lang.strip(), lines))

        elif start3 == earliest:
            depth = 0
            j = start3 + 8
            start_content = j
            while j < len(template):
                if template[j] == '[':
                    depth += 1
                elif template[j] == ']':
                    if depth == 0:
                        break
                    depth -= 1
                j += 1

            content = template[start_content:j]
            i = j + 1

            import re
            rows = []
            for row_m in re.finditer(r'\[(.*?)\]', content, re.DOTALL):
                row_str = row_m.group(1)
                cells = re.findall(r'"([^"]*)"', row_str)
                rows.append(cells)

            html_parts.append(render_table(rows))

        elif start4 == earliest:
            end = template.find("}", i + 9)
            inner = template[i + 9:end]
            i = end + 1

            parts = inner.split("|", 2)
            if len(parts) >= 3:
                type_, title, body = parts[0], parts[1], parts[2]
            elif len(parts) == 2:
                type_, title, body = parts[0], parts[1], ""
            else:
                continue

            html_parts.append(render_callout(type_, title, body))

        else:
            i += 1

    return "".join(html_parts)


def build_nav():
    parts = []
    for group in NAV:
        parts.append(f'<div class="toc-part">{group["part"]}</div>')
        for label, href in group["links"]:
            parts.append(f'<a class="toc-link" href="{href}">{esc(label)}</a>')
    return "\n".join(parts)


def build_sections():
    parts = []
    for section in SECTIONS:
        content = parse_content(section["content"])
        parts.append(f'<section id="{section["id"]}"><h3><span class="sec-num">{section["num"]}</span>{esc(section["title"])}</h3>{content}</section>')
    return "\n".join(parts)


PART_MAPPINGS = {
    "s0": {"id": "part0", "label": "Part 0", "title": "Prerequisites"},
    "s1": {"id": "part1", "label": "Part 1", "title": "Master Setup"},
    "s2": {"id": "part2", "label": "Part 2", "title": "Worker Setup"},
    "s3": {"id": "part3", "label": "Part 3", "title": "Portability Test"},
}


def build_content():
    """Interleave part dividers with their sections — not all parts first."""
    intros = {
        "part0": "Install these tools on <strong>every machine</strong> — both master and all workers. Do this once before running any setup script.",
        "part1": "Run these steps on the laptop that will act as the cluster master. It coordinates all computation and hosts the API.",
        "part2": "Run these steps on every laptop that will join the cluster as a worker. The master must already be running (Part 1 complete) before you start here.",
        "part3": "These instructions are for the group that is <strong>testing Group 03's output</strong>. Follow them from any machine on the same LAN as the Group 03 master.",
    }

    chunks = []
    seen_parts = set()
    for section in SECTIONS:
        prefix = section["id"].split("-")[0]  # "s0", "s1", etc.
        if prefix not in seen_parts:
            seen_parts.add(prefix)
            info = PART_MAPPINGS[prefix]
            chunks.append(f'<div class="part-divider" id="{info["id"]}"><div class="part-label">{info["label"]}</div><div class="part-title">{esc(info["title"])}</div></div><p style="color:var(--ink-3);font-size:13.5px;margin-top:12px;">{intros[info["id"]]}</p>')
        content = parse_content(section["content"])
        chunks.append(f'<section id="{section["id"]}"><h3><span class="sec-num">{section["num"]}</span>{esc(section["title"])}</h3>{content}</section>')
    return "\n".join(chunks)


def generate():
    nav_html = build_nav()
    content_html = build_content()

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Group 03 &mdash; PageRank Cluster Manual</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=Sora:wght@300;400;600;700;800&display=swap" rel="stylesheet">
<style>
{CSS}
</style>
</head>
<body>
<button class="hamburger" id="hamburger" aria-label="Toggle navigation"><span></span><span></span><span></span></button>
<div class="layout">
<nav class="sidebar" id="sidebar">
  <div class="sidebar-header">
    <div class="sidebar-logo">Group 03</div>
    <div class="sidebar-title">PageRank Cluster Manual</div>
  </div>
  <div class="toc">
{nav_html}
  </div>
</nav>
<main class="main">
<div class="cover">
  <div class="cover-inner">
    <div class="cover-badge">GROUP 03 &middot; CSCS2543 &middot; Section H3</div>
    <h1>Network Graph<br>PageRank Cluster</h1>
    <div class="cover-sub">Setup &amp; Portability Manual &mdash; May 11, 2026</div>
    <div class="cover-chips">
      <span class="chip">Apache Spark 3.5.3</span>
      <span class="chip">Hadoop HDFS 3.3.6</span>
      <span class="chip">Stanford Web-Google</span>
      <span class="chip">875K nodes &middot; 5M edges</span>
      <span class="chip">macOS &middot; Linux &middot; Windows</span>
    </div>
  </div>
</div>
<div class="content">
{content_html}
</div>
<footer>Group 03 &mdash; CSCS2543 &mdash; Section H3 &mdash; May 11, 2026</footer>
</main>
</div>
<script>
{JAVASCRIPT}
</script>
</body>
</html>
"""
    return html


if __name__ == "__main__":
    output = generate()
    out_path = Path(__file__).parent / "index.html"
    out_path.write_text(output)
    print(f"Generated: {out_path}")
    print(f"Size: {len(output):,} bytes")
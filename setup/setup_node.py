"""
setup_node.py — Cross-platform cluster node setup.
Works on macOS, Linux, and Windows (Python 3.8+).

Usage:
  python3 setup/setup_node.py --role master
  python3 setup/setup_node.py --role worker
"""

import sys
import os
import shutil
import subprocess
import argparse
import urllib.request
import tarfile
import zipfile
import platform
from pathlib import Path

# Add setup dir to path so we can import config
sys.path.insert(0, str(Path(__file__).parent))
from config import (
    MASTER_IP, HADOOP_VERSION, SPARK_VERSION, JAVA_VERSION,
    HADOOP_HOME, SPARK_HOME, DATA_ROOT, INSTALL_ROOT,
    IS_MAC, IS_LINUX, IS_WINDOWS, SBIN_EXT,
    get_local_ip, find_java_home, verify_java, SPARK_MASTER_URL
)

LOCAL_IP = get_local_ip()


# ── Helpers ───────────────────────────────────────────────────────────────────

def die(msg):
    print(f"\n✗  ERROR: {msg}", file=sys.stderr)
    sys.exit(1)

def ok(msg):
    print(f"  ✓  {msg}")

def section(title):
    print(f"\n── {title} {'─' * max(0, 48 - len(title))}")

def run(cmd, check=True, shell=False, capture=False):
    """Run a command list or string. On Windows, shell=True for builtins."""
    if IS_WINDOWS and isinstance(cmd, list):
        shell = True
        cmd = " ".join(f'"{c}"' if " " in str(c) else str(c) for c in cmd)
    kwargs = dict(check=check, shell=shell)
    if capture:
        kwargs.update(stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return subprocess.run(cmd, **kwargs)

def sudo_run(cmd_list):
    """Run with elevated privileges (sudo on unix, plain on windows — run as admin)."""
    if IS_WINDOWS:
        run(cmd_list)
    else:
        run(["sudo"] + cmd_list)

def mkdir(path, as_sudo=False):
    path = Path(path)
    if not path.exists():
        if as_sudo and not IS_WINDOWS:
            run(["sudo", "mkdir", "-p", str(path)])
        else:
            path.mkdir(parents=True, exist_ok=True)

def chown(path):
    """Give current user ownership of a directory (Unix only)."""
    if not IS_WINDOWS:
        user = os.environ.get("USER", os.environ.get("LOGNAME", ""))
        if user:
            run(["sudo", "chown", "-R", f"{user}:{user}", str(path)], check=False)

def download(url, dest):
    dest = Path(dest)
    if dest.exists():
        ok(f"Already downloaded: {dest.name}")
        return
    print(f"  Downloading {dest.name}...")

    def progress(count, block, total):
        if total > 0:
            pct = min(100, int(count * block * 100 / total))
            bar = "█" * (pct // 5) + "░" * (20 - pct // 5)
            print(f"\r    [{bar}] {pct}%", end="", flush=True)

    urllib.request.urlretrieve(url, dest, reporthook=progress)
    print()


def extract_tar(archive, dest):
    dest = Path(dest)
    if not dest.exists():
        print(f"  Extracting {Path(archive).name}...")
        with tarfile.open(archive) as tf:
            tf.extractall(str(dest.parent))
        ok(f"Extracted to {dest}")
    else:
        ok(f"Already extracted: {dest}")


# ── Java ──────────────────────────────────────────────────────────────────────

def install_java():
    section(f"Java {JAVA_VERSION}")
    if verify_java():
        return

    if IS_LINUX:
        run(["sudo", "apt-get", "update", "-q"])
        run(["sudo", "apt-get", "install", "-y", "-q", f"openjdk-{JAVA_VERSION}-jdk"])
    elif IS_MAC:
        if shutil.which("brew"):
            run(["brew", "install", f"openjdk@{JAVA_VERSION}"])
            # Symlink so it's on PATH
            brew_prefix = subprocess.check_output(["brew", "--prefix"], text=True).strip()
            jdk_bin = Path(brew_prefix) / f"opt/openjdk@{JAVA_VERSION}/bin"
            profile = Path.home() / (".zprofile" if Path.home().joinpath(".zprofile").exists() else ".bash_profile")
            export_line = f'\nexport PATH="{jdk_bin}:$PATH"\n'
            with open(profile, "a") as f:
                f.write(export_line)
            print(f"  Added Java to {profile}. Run: source {profile}")
        else:
            die("Homebrew not found. Install from https://brew.sh then re-run.")
    elif IS_WINDOWS:
        if shutil.which("winget"):
            run(["winget", "install", "EclipseAdoptium.Temurin.11.JDK", "--silent"], check=False)
        else:
            die("Install Java 11 manually from https://adoptium.net then re-run.")

    if not verify_java():
        die("Java install failed. Please install Java 11 manually and re-run.")


# ── Python deps ───────────────────────────────────────────────────────────────

def install_python_deps():
    section("Python dependencies")
    pkgs = ["pyspark", "flask", "requests"]
    pip = [sys.executable, "-m", "pip", "install", "-q"] + pkgs
    if IS_LINUX:
        pip += ["--break-system-packages"]
    run(pip, check=False)
    ok(f"Installed: {', '.join(pkgs)}")


# ── Hadoop ────────────────────────────────────────────────────────────────────

def install_hadoop(role):
    section(f"Hadoop {HADOOP_VERSION} ({role})")

    TMP = Path.home() / "Downloads"
    TMP.mkdir(exist_ok=True)

    archive = TMP / f"hadoop-{HADOOP_VERSION}.tar.gz"
    url = f"https://downloads.apache.org/hadoop/common/hadoop-{HADOOP_VERSION}/hadoop-{HADOOP_VERSION}.tar.gz"

    mkdir(INSTALL_ROOT, as_sudo=True)
    download(url, archive)

    if not HADOOP_HOME.exists():
        if IS_WINDOWS:
            # Extract to INSTALL_ROOT
            INSTALL_ROOT.mkdir(parents=True, exist_ok=True)
            extract_tar(archive, HADOOP_HOME)
        else:
            run(["sudo", "tar", "-xzf", str(archive), "-C", str(INSTALL_ROOT)])
        ok(f"Hadoop at {HADOOP_HOME}")
    else:
        ok(f"Hadoop already at {HADOOP_HOME}")

    # Windows needs winutils.exe for HDFS to work
    if IS_WINDOWS:
        _install_winutils()

    java_home = find_java_home()
    if not java_home:
        die("Cannot find JAVA_HOME. Set it manually in your environment.")

    _write_hadoop_configs(role, java_home)

    mkdir(DATA_ROOT / "namenode", as_sudo=True)
    mkdir(DATA_ROOT / "datanode", as_sudo=True)
    chown(DATA_ROOT)
    chown(HADOOP_HOME)

    ok("Hadoop configured")


def _install_winutils():
    """Download winutils.exe for Hadoop on Windows."""
    winutils_dir = HADOOP_HOME / "bin"
    winutils_exe = winutils_dir / "winutils.exe"
    if winutils_exe.exists():
        ok("winutils.exe already present")
        return
    url = f"https://github.com/cdarlint/winutils/raw/master/hadoop-{HADOOP_VERSION}/bin/winutils.exe"
    print(f"  Downloading winutils.exe (required for Hadoop on Windows)...")
    try:
        download(url, winutils_exe)
        ok("winutils.exe installed")
    except Exception as e:
        print(f"  ⚠  Could not auto-download winutils.exe: {e}")
        print(f"  Download manually from: https://github.com/cdarlint/winutils")
        print(f"  Place winutils.exe in: {winutils_dir}")


def _write_hadoop_configs(role, java_home):
    conf = HADOOP_HOME / "etc" / "hadoop"

    (conf / "core-site.xml").write_text(f"""<?xml version="1.0"?>
<configuration>
  <property><name>fs.defaultFS</name><value>hdfs://{MASTER_IP}:9000</value></property>
  <property><name>hadoop.tmp.dir</name><value>/tmp/hadoop-data</value></property>
</configuration>
""")

    (conf / "hdfs-site.xml").write_text(f"""<?xml version="1.0"?>
<configuration>
  <property><name>dfs.replication</name><value>3</value></property>
  <property><name>dfs.namenode.name.dir</name><value>file:///{DATA_ROOT}/namenode</value></property>
  <property><name>dfs.datanode.data.dir</name><value>file:///{DATA_ROOT}/datanode</value></property>
  <property><name>dfs.namenode.datanode.registration.ip-hostname-check</name><value>false</value></property>
</configuration>
""")

    (conf / "mapred-site.xml").write_text("""<?xml version="1.0"?>
<configuration>
  <property><name>mapreduce.framework.name</name><value>yarn</value></property>
</configuration>
""")

    # hadoop-env — must set JAVA_HOME here for Hadoop daemons
    env_file = conf / "hadoop-env.sh"
    env_content = env_file.read_text() if env_file.exists() else ""
    if "JAVA_HOME" not in env_content:
        with open(env_file, "a") as f:
            f.write(f"\nexport JAVA_HOME={java_home}\n")

    if IS_WINDOWS:
        env_cmd = conf / "hadoop-env.cmd"
        with open(env_cmd, "a") as f:
            f.write(f"\nset JAVA_HOME={java_home}\n")

    # Workers file (master only — worker IPs added later)
    if role == "master":
        (conf / "workers").write_text("localhost\n")


# ── Spark ─────────────────────────────────────────────────────────────────────

def install_spark(role):
    section(f"Spark {SPARK_VERSION} ({role})")

    TMP = Path.home() / "Downloads"
    archive = TMP / f"spark-{SPARK_VERSION}-bin-hadoop3.tgz"
    url = f"https://downloads.apache.org/spark/spark-{SPARK_VERSION}/spark-{SPARK_VERSION}-bin-hadoop3.tgz"

    download(url, archive)

    if not SPARK_HOME.exists():
        if IS_WINDOWS:
            INSTALL_ROOT.mkdir(parents=True, exist_ok=True)
            extract_tar(archive, SPARK_HOME)
            extracted = INSTALL_ROOT / f"spark-{SPARK_VERSION}-bin-hadoop3"
            if extracted.exists() and not SPARK_HOME.exists():
                extracted.rename(SPARK_HOME)
        else:
            run(["sudo", "tar", "-xzf", str(archive), "-C", str(INSTALL_ROOT)])
            extracted = INSTALL_ROOT / f"spark-{SPARK_VERSION}-bin-hadoop3"
            if extracted.exists():
                run(["sudo", "mv", str(extracted), str(SPARK_HOME)])
        ok(f"Spark at {SPARK_HOME}")
    else:
        ok(f"Spark already at {SPARK_HOME}")

    chown(SPARK_HOME)

    java_home = find_java_home()
    conf = SPARK_HOME / "conf"

    # spark-env
    env_src = conf / "spark-env.sh.template"
    env_dst = conf / "spark-env.sh"
    if env_src.exists() and not env_dst.exists():
        shutil.copy(env_src, env_dst)

    local_ip = MASTER_IP if role == "master" else LOCAL_IP

    with open(env_dst, "a") as f:
        f.write(f"\nexport JAVA_HOME={java_home}\n")
        f.write(f"export SPARK_LOCAL_IP={local_ip}\n")
        f.write(f"export PYSPARK_PYTHON={sys.executable}\n")
        if role == "master":
            f.write(f"export SPARK_MASTER_HOST={MASTER_IP}\n")

    # Windows: spark-env.cmd
    if IS_WINDOWS:
        env_cmd = conf / "spark-env.cmd"
        with open(env_cmd, "w") as f:
            f.write(f"set JAVA_HOME={java_home}\n")
            f.write(f"set SPARK_LOCAL_IP={local_ip}\n")
            f.write(f"set PYSPARK_PYTHON={sys.executable}\n")
            if role == "master":
                f.write(f"set SPARK_MASTER_HOST={MASTER_IP}\n")

    # spark-defaults
    defaults = conf / "spark-defaults.conf"
    defaults.write_text(
        f"spark.master                     {SPARK_MASTER_URL}\n"
        f"spark.executor.memory            2g\n"
        f"spark.driver.memory              1g\n"
        f"spark.serializer                 org.apache.spark.serializer.KryoSerializer\n"
        f"spark.default.parallelism        12\n"
    )

    # Workers file (master only)
    if role == "master":
        (conf / "workers").write_text("localhost\n")

    ok("Spark configured")


# ── Format NameNode ───────────────────────────────────────────────────────────

def format_namenode():
    nn_current = DATA_ROOT / "namenode" / "current"
    if nn_current.exists():
        ok("NameNode already formatted — skipping")
        return
    print("  Formatting NameNode...")
    hdfs = HADOOP_HOME / "bin" / ("hdfs.cmd" if IS_WINDOWS else "hdfs")
    run([str(hdfs), "namenode", "-format", "-nonInteractive", "-force"])
    ok("NameNode formatted")


# ── Start services ────────────────────────────────────────────────────────────

def start_master_services():
    section("Starting services (master)")
    sbin = HADOOP_HOME / "sbin"

    # Start HDFS
    start_dfs = sbin / f"start-dfs{SBIN_EXT}"
    run([str(start_dfs)])

    import time; time.sleep(4)

    # Start Spark Master
    start_master = SPARK_HOME / "sbin" / f"start-master{SBIN_EXT}"
    run([str(start_master)])

    time.sleep(2)

    # Create HDFS dirs
    hdfs = HADOOP_HOME / "bin" / ("hdfs.cmd" if IS_WINDOWS else "hdfs")
    run([str(hdfs), "dfs", "-mkdir", "-p", "/pagerank/input"],  check=False)
    run([str(hdfs), "dfs", "-mkdir", "-p", "/pagerank/output"], check=False)

    ok("HDFS and Spark Master started")
    print(f"\n  Spark UI → http://{MASTER_IP}:8080")
    print(f"  HDFS UI  → http://{MASTER_IP}:9870")


def start_worker_services():
    section("Starting services (worker)")
    sbin = HADOOP_HOME / "sbin"

    # Start DataNode
    start_dn = sbin / f"hadoop-daemon{SBIN_EXT}"
    if not start_dn.exists():
        start_dn = sbin / ("hadoop-daemon.sh" if not IS_WINDOWS else "hadoop-daemon.cmd")
    run([str(start_dn), "start", "datanode"])

    import time; time.sleep(2)

    # Start Spark Worker
    start_worker = SPARK_HOME / "sbin" / f"start-worker{SBIN_EXT}"
    run([str(start_worker), SPARK_MASTER_URL])

    ok(f"DataNode and Spark Worker started (this machine: {LOCAL_IP})")
    print(f"\n  Tell master to register this worker:")
    print(f"  echo '{LOCAL_IP}' >> {HADOOP_HOME}/etc/hadoop/workers")
    print(f"  echo '{LOCAL_IP}' >> {SPARK_HOME}/conf/workers")


# ── Verify ────────────────────────────────────────────────────────────────────

def verify(role):
    section("Verification")
    print("  Running jps (Java process check):")

    jps = shutil.which("jps") or str(find_java_home() / "bin" / "jps")
    try:
        out = subprocess.check_output([jps], text=True)
        print(out)
        if role == "master":
            required = ["NameNode", "DataNode", "Master"]
            missing  = [p for p in required if p not in out]
            if missing:
                print(f"  ⚠  Missing processes: {missing}")
                print(f"     Check logs at: {HADOOP_HOME}/logs/  and  {SPARK_HOME}/logs/")
            else:
                ok("All required processes running")
        else:
            for proc in ["DataNode", "Worker"]:
                status = "✓" if proc in out else "✗  MISSING"
                print(f"  {status}  {proc}")
    except Exception as e:
        print(f"  Could not run jps: {e}")

    if role == "master":
        print(f"\n  Open in browser:")
        print(f"    Spark → http://{MASTER_IP}:8080")
        print(f"    HDFS  → http://{MASTER_IP}:9870")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Cluster node setup (cross-platform)")
    parser.add_argument("--role", choices=["master", "worker"], required=True,
                        help="master or worker")
    args = parser.parse_args()
    role = args.role

    print(f"\n{'═'*52}")
    print(f"  Group 03 · PageRank Cluster — {role.upper()} SETUP")
    print(f"  OS        : {platform.system()} {platform.machine()}")
    print(f"  This IP   : {LOCAL_IP}")
    print(f"  Master IP : {MASTER_IP}")
    print(f"{'═'*52}")

    if MASTER_IP == "192.168.1.100":
        print("\n  ⚠  MASTER_IP is still the default value.")
        print("     Edit setup/config.py and set it to your actual LAN IP.")
        ans = input("     Continue anyway? [y/N]: ").strip().lower()
        if ans != "y":
            sys.exit(0)

    install_java()
    install_python_deps()
    install_hadoop(role)
    install_spark(role)

    if role == "master":
        format_namenode()
        start_master_services()
    else:
        start_worker_services()

    verify(role)

    print(f"\n{'═'*52}")
    print(f"  ✓  {role.capitalize()} setup complete")
    if role == "master":
        print(f"\n  Next steps:")
        print(f"    1. Run worker_setup on each worker laptop")
        print(f"    2. Add worker IPs to workers files (printed by each worker)")
        print(f"    3. python3 src/download_dataset.py")
    else:
        print(f"\n  Next: register this IP ({LOCAL_IP}) with the master (see above)")
    print(f"{'═'*52}\n")


if __name__ == "__main__":
    main()

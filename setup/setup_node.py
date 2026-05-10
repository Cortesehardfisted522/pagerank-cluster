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

def die(msg, hint=None):
    print(f"\n✗  ERROR: {msg}", file=sys.stderr)
    if hint:
        print(f"  → {hint}", file=sys.stderr)
    sys.exit(1)

def warn(msg, hint=None):
    print(f"\n⚠  WARNING: {msg}")
    if hint:
        print(f"  → {hint}")

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
    try:
        return subprocess.run(cmd, **kwargs)
    except FileNotFoundError:
        cmd_name = cmd.split()[0] if isinstance(cmd, str) else cmd[0]
        die(
            f"'{cmd_name}' not found — is it installed and on your PATH?",
            f"Verify the prerequisite is installed before re-running this script."
        )
    except PermissionError:
        die(
            f"Permission denied running: {cmd}",
            "Try running as administrator (Windows) or with sudo (macOS/Linux)."
        )
    except OSError as e:
        if "no such file" in str(e).lower():
            cmd_name = cmd.split()[0] if isinstance(cmd, str) else cmd[0]
            die(f"'{cmd_name}' not found or not executable.", "Check that the prerequisite is installed.")
        raise

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
        try:
            import pwd
            user = pwd.getpwuid(os.getuid()).pw_name
            # On macOS, group assignment can fail; use user-only chown for safety
            run(["sudo", "chown", "-R", user, str(path)], check=False)
        except Exception:
            # Keep setup moving even if ownership normalization fails.
            run(["sudo", "chown", "-R", os.environ.get("USER", "root"), str(path)], check=False)

def download(url, dest):
    dest = Path(dest)
    if dest.exists():
        ok(f"Already downloaded: {dest.name}")
        return
    print(f"  Downloading {dest.name}...")
    tmp_dest = Path(f"{dest}.part")

    def progress(count, block, total):
        if total > 0:
            pct = min(100, int(count * block * 100 / total))
            bar = "█" * (pct // 5) + "░" * (20 - pct // 5)
            print(f"\r    [{bar}] {pct}%", end="", flush=True)

    import ssl
    ssl_context = None
    try:
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
    except Exception:
        ssl_context = None

    try:
        if ssl_context:
            with urllib.request.urlopen(url, context=ssl_context) as response:
                total = response.headers.get('Content-Length', 0)
                with open(tmp_dest, 'wb') as f:
                    downloaded = 0
                    block_size = 8192
                    while True:
                        chunk = response.read(block_size)
                        if not chunk:
                            break
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total:
                            progress(downloaded, 1, int(total))
        else:
            urllib.request.urlretrieve(url, tmp_dest, reporthook=progress)
        tmp_dest.replace(dest)
        print()
    except urllib.error.HTTPError as e:
        print()
        warn(f"HTTP error {e.code} downloading {dest.name} from {url}")
        hint = (
            "The download URL may have moved. "
            "Try running the script again — it will use fallback mirrors automatically."
        )
        die(f"Download failed (HTTP {e.code})", hint)
    except urllib.error.URLError as e:
        print()
        die(
            f"Could not reach {url}",
            "Check your internet connection. Proxy or firewall may be blocking outbound HTTPS."
        )
    except ssl.SSLCertVerificationError:
        print()
        die(
            "SSL certificate verification failed",
            "Your Python installation may have an incomplete certificate store. "
            "On macOS: pip3 install --upgrade certifi  &&  /Applications/Python\\ 3.*/Install\\ Certificates.command"
        )
    except Exception:
        print()
        if tmp_dest.exists():
            tmp_dest.unlink(missing_ok=True)
        raise


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
        result = run(["sudo", "apt-get", "update", "-q"], check=False, capture=True)
        if result.returncode != 0:
            warn("apt-get update failed", "Check your apt sources and internet connection.")
        result = run(["sudo", "apt-get", "install", "-y", "-q", f"openjdk-{JAVA_VERSION}-jdk"], check=False)
        if result.returncode != 0:
            die(
                f"openjdk-{JAVA_VERSION}-jdk package failed to install",
                "Try: sudo apt-get install -y openjdk-11-jdk   or   sudo apt-get install -y openjdk-17-jdk"
            )
    elif IS_MAC:
        if shutil.which("brew"):
            result = run(["brew", "install", f"openjdk@{JAVA_VERSION}"], check=False)
            if result.returncode != 0:
                die(
                    f"brew install openjdk@{JAVA_VERSION} failed",
                    "Try manually: brew install openjdk@11   or   brew install openjdk@17"
                )
            brew_prefix = subprocess.check_output(["brew", "--prefix"], text=True).strip()
            jdk_bin = Path(brew_prefix) / f"opt/openjdk@{JAVA_VERSION}/bin"
            profile = Path.home() / (".zprofile" if Path.home().joinpath(".zprofile").exists() else ".bash_profile")
            export_line = f'\nexport PATH="{jdk_bin}:$PATH"\n'
            with open(profile, "a") as f:
                f.write(export_line)
            print(f"  Added Java to {profile}. Run: source {profile}")
        else:
            die(
                "Homebrew not found",
                "Install Homebrew: /bin/bash -c \"$(curl -fsSL https://brew.sh)\"  Then re-run this script."
            )
    elif IS_WINDOWS:
        if shutil.which("winget"):
            result = run(["winget", "install", "EclipseAdoptium.Temurin.17.JDK", "--silent"], check=False)
            if result.returncode != 0:
                warn(
                    "winget install failed — Java was not installed automatically",
                    "Download Java 17 from: https://adoptium.net/temurin/releases/?version=17&os=windows&arch=x64&package=jdk"
                )
        else:
            die(
                "winget not found",
                "Download Java 17 from: https://adoptium.net/temurin/releases/?version=17&os=windows&arch=x64&package=jdk  (.msi installer)"
            )

    if not verify_java():
        java_version = subprocess.run(["java", "-version"], capture=True, text=True, stderr=subprocess.STDOUT)
        current = java_version.stdout.splitlines()[0] if java_version.stdout else "(not found)"
        die(
            f"Java {JAVA_VERSION} not found after install. Current: {current}",
            f"Install Java 11 or 17 manually, then re-run this script."
        )


# ── Python deps ───────────────────────────────────────────────────────────────

def install_python_deps():
    section("Python dependencies")
    pkgs = ["pyspark", "flask", "requests"]
    pip = [sys.executable, "-m", "pip", "install", "-q"] + pkgs
    if IS_LINUX:
        pip += ["--break-system-packages"]
    result = run(pip, check=False, capture=True)
    if result.returncode != 0:
        warn(
            f"pip install failed — pyspark/flask/requests may not be installed",
            f"Try manually: {' '.join(pip)}"
        )
    ok(f"Installed: {', '.join(pkgs)}")


# ── Hadoop ────────────────────────────────────────────────────────────────────

def install_hadoop(role):
    section(f"Hadoop {HADOOP_VERSION} ({role})")

    if IS_WINDOWS:
        TMP = Path("C:/temp_hadoop")
        TMP.mkdir(exist_ok=True)
    else:
        TMP = Path.home() / "Downloads"
        TMP.mkdir(exist_ok=True)

    archive = TMP / f"hadoop-{HADOOP_VERSION}.tar.gz"
    url = f"https://downloads.apache.org/hadoop/common/hadoop-{HADOOP_VERSION}/hadoop-{HADOOP_VERSION}.tar.gz"

    mkdir(INSTALL_ROOT, as_sudo=True)
    download(url, archive)

    if not HADOOP_HOME.exists():
        try:
            if IS_WINDOWS:
                INSTALL_ROOT.mkdir(parents=True, exist_ok=True)
                extract_tar(archive, HADOOP_HOME)
            else:
                run(["sudo", "tar", "-xzf", str(archive), "-C", str(INSTALL_ROOT)])
        except Exception as e:
            if "Permission denied" in str(e) or "EACCES" in str(e):
                die(
                    f"Permission denied writing to {INSTALL_ROOT}",
                    "The install directory requires admin access. "
                    "On macOS/Linux: ensure you entered your sudo password correctly. "
                    "On Windows: re-run as Administrator."
                )
            raise
        ok(f"Hadoop at {HADOOP_HOME}")
    else:
        ok(f"Hadoop already at {HADOOP_HOME}")

    if IS_WINDOWS:
        _install_winutils()

    java_home = find_java_home()
    if not java_home:
        die(
            "Cannot find JAVA_HOME",
            "Set JAVA_HOME in your environment:  set JAVA_HOME=C:\\Program Files\\Eclipse Adoptium\\jdk-17...  (Windows)  "
            "or  export JAVA_HOME=/usr/lib/jvm/java-17...  (macOS/Linux)"
        )

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
            # Suppress sun.misc.Unsafe warnings on macOS/Java 11
            if IS_MAC:
                f.write("export HADOOP_OPTS=\"-Djava.security.egd=file:/dev/./urandom -XX:+IgnoreUnrecognizedVMOptions -XX:+UseParallelGC\"\n")

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

    # Use shorter path on Windows to avoid 260-character path limit
    if IS_WINDOWS:
        TMP = Path("C:/temp_spark")
        TMP.mkdir(exist_ok=True)
    else:
        TMP = Path.home() / "Downloads"

    archive = TMP / f"spark-{SPARK_VERSION}-bin-hadoop3.tgz"
    primary_url = f"https://downloads.apache.org/spark/spark-{SPARK_VERSION}/spark-{SPARK_VERSION}-bin-hadoop3.tgz"
    archive_url = f"https://archive.apache.org/dist/spark/spark-{SPARK_VERSION}/spark-{SPARK_VERSION}-bin-hadoop3.tgz"
    # Additional fallback mirrors
    mirror_urls = [
        "https://dlcdn.apache.org/spark/spark-%s/spark-%s-bin-hadoop3.tgz" % (SPARK_VERSION, SPARK_VERSION),
        "https://mirrors.ocf.berkeley.edu/apache/spark/spark-%s/spark-%s-bin-hadoop3.tgz" % (SPARK_VERSION, SPARK_VERSION),
    ]

    if not archive.exists():
        last_error = None
        for url in [primary_url, archive_url] + mirror_urls:
            try:
                download(url, archive)
                break
            except Exception as e:
                last_error = e
                print(f"  ⚠  Could not download from {url}: {e}")
        else:
            die(
                f"Spark {SPARK_VERSION} download failed from all mirrors",
                "The version may have been retired. "
                "Try updating SPARK_VERSION in setup/config.py to a newer release "
                "(check available versions at https://spark.apache.org/downloads.html)"
            )
    else:
        ok(f"Already downloaded: {archive.name}")

    if not SPARK_HOME.exists():
        try:
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
        except Exception as e:
            if "Permission denied" in str(e) or "EACCES" in str(e):
                die(
                    f"Permission denied writing to {INSTALL_ROOT}",
                    "Ensure you have admin/sudo access. On Windows: re-run as Administrator."
                )
            raise
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
        # Fix macOS native library username resolution issue
        if IS_MAC:
            f.write("export SPARK_NO_DAEMONIZE=true\n")
            f.write("export HADOOP_OPTS=\"-Djava.library.path=\\$HADOOP_HOME/lib/native\"\n")
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
    jps = shutil.which("jps") or str(find_java_home() / "bin" / "jps" if find_java_home() else "jps")
    try:
        out = subprocess.check_output([jps], text=True)
        if "NameNode" in out:
            ok("NameNode already running — skipping format")
            return
    except FileNotFoundError:
        warn(
            "jps not found",
            "JAVA_HOME may not be set correctly. Check that Java is installed and on your PATH."
        )
    except Exception:
        pass

    nn_current = DATA_ROOT / "namenode" / "current"
    if nn_current.exists():
        ok("NameNode already formatted — skipping")
        return
    print("  Formatting NameNode...")
    hdfs = HADOOP_HOME / "bin" / ("hdfs.cmd" if IS_WINDOWS else "hdfs")
    result = run([str(hdfs), "namenode", "-format", "-nonInteractive", "-force"], check=False, capture=True)
    if result.returncode != 0:
        err = result.stderr if result.stderr else result.stdout
        if "cannot be formatted" in err.lower() or "already running" in err.lower():
            warn(
                "NameNode cannot be formatted — a NameNode process is already running",
                "Stop the running NameNode first:  stop-dfs.sh   (macOS/Linux)   or   stop-dfs.cmd   (Windows)"
            )
        else:
            warn(
                f"NameNode format failed (exit {result.returncode})",
                f"Check Hadoop logs in: {HADOOP_HOME}/logs/"
            )
            print(f"  Error output: {err[:500]}")
    else:
        ok("NameNode formatted")


# ── Start services ────────────────────────────────────────────────────────────

def check_ssh():
    """Verify SSH (Remote Login) is enabled on macOS."""
    if IS_MAC:
        try:
            out = subprocess.check_output(
                ["sudo", "systemsetup", "-getremotelogin"], text=True
            )
            if "On" not in out:
                warn(
                    "SSH Remote Login is not enabled — Hadoop daemons may fail to communicate",
                    "Enable it: System Settings → General → Remote Login → ON   OR   sudo systemsetup -setremotelogin on"
                )
        except FileNotFoundError:
            warn(
                "systemsetup not found",
                "Ensure macOS admin tools are available, then re-run."
            )
        except Exception:
            pass


def start_master_services():
    section("Starting services (master)")
    check_ssh()

    sbin = HADOOP_HOME / "sbin"
    start_dfs = sbin / f"start-dfs{SBIN_EXT}"
    result = run([str(start_dfs)], check=False, capture=True)
    if result.returncode != 0:
        err = result.stderr if result.stderr else result.stdout
        if "ssh" in err.lower() or "connection refused" in err.lower():
            warn(
                "start-dfs.sh failed — likely an SSH connectivity issue",
                "Enable SSH Remote Login on macOS: System Settings → General → Remote Login → ON  "
                "OR  sudo systemsetup -setremotelogin on"
            )
        elif "permission denied" in err.lower():
            warn(
                "start-dfs.sh failed — permission denied",
                "Ensure your user has sudo access, or re-run with appropriate permissions."
            )
        else:
            warn(f"HDFS startup had issues (exit {result.returncode}). Check {HADOOP_HOME}/logs/")

    import time; time.sleep(4)

    start_master = SPARK_HOME / "sbin" / f"start-master{SBIN_EXT}"
    result = run([str(start_master)], check=False, capture=True)
    if result.returncode != 0:
        err = result.stderr if result.stderr else result.stdout
        if "user" in err.lower() and ("unknown" in err.lower() or "not found" in err.lower()):
            warn(
                "Spark Master failed to start — username resolution error on macOS",
                "This is a known macOS/Java compatibility issue. "
                "The cluster will still function; restart Spark manually if workers can't connect."
            )
        else:
            warn(
                f"Spark Master startup had issues (exit {result.returncode}). Check {SPARK_HOME}/logs/"
            )
            print(f"  Error: {err[:300]}")

    time.sleep(2)

    hdfs = HADOOP_HOME / "bin" / ("hdfs.cmd" if IS_WINDOWS else "hdfs")
    run([str(hdfs), "dfs", "-mkdir", "-p", "/pagerank/input"],  check=False)
    run([str(hdfs), "dfs", "-mkdir", "-p", "/pagerank/output"], check=False)

    ok("HDFS and Spark Master started")
    print(f"\n  Spark UI → http://{MASTER_IP}:8080")
    print(f"  HDFS UI  → http://{MASTER_IP}:9870")


def start_worker_services():
    section("Starting services (worker)")
    sbin = HADOOP_HOME / "sbin"

    start_dn = sbin / f"hadoop-daemon{SBIN_EXT}"
    if not start_dn.exists():
        start_dn = sbin / ("hadoop-daemon.sh" if not IS_WINDOWS else "hadoop-daemon.cmd")
    result = run([str(start_dn), "start", "datanode"], check=False, capture=True)
    if result.returncode != 0:
        err = result.stderr if result.stderr else result.stdout
        if "ssh" in err.lower() or "connection refused" in err.lower():
            warn(
                "DataNode failed to start — SSH issue",
                "Enable SSH Remote Login: System Settings → General → Remote Login → ON  OR  sudo systemsetup -setremotelogin on"
            )
        else:
            warn(
                f"DataNode startup had issues (exit {result.returncode}). Check {HADOOP_HOME}/logs/"
            )
            print(f"  Error: {err[:300]}")

    import time; time.sleep(2)

    start_worker = SPARK_HOME / "sbin" / f"start-worker{SBIN_EXT}"
    result = run([str(start_worker), SPARK_MASTER_URL], check=False, capture=True)
    if result.returncode != 0:
        err = result.stderr if result.stderr else result.stdout
        if "connection refused" in err.lower():
            warn(
                f"Spark Worker cannot reach master at {MASTER_IP}:7077",
                f"Verify MASTER_IP={MASTER_IP} is correct and the master is running. "
                "Check firewall: ports 7077, 9000, 9866 must be open on both machines."
            )
        elif "user" in err.lower() and ("unknown" in err.lower() or "not found" in err.lower()):
            warn(
                "Spark Worker failed — macOS username resolution error",
                "This is a known macOS/Java compatibility issue. "
                "The worker may still connect; check the Spark UI at the master's port 8080."
            )
        else:
            warn(
                f"Spark Worker startup had issues (exit {result.returncode}). Check {SPARK_HOME}/logs/"
            )
            print(f"  Error: {err[:300]}")

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

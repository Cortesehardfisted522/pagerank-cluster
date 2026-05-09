"""
config.py — Shared configuration for all setup scripts.
Edit MASTER_IP below, then run setup_node.py.
Works on macOS, Linux, and Windows.
"""

import sys
import os
import platform
import socket
import subprocess
from pathlib import Path

# ── ONLY THING YOU NEED TO CHANGE ─────────────────────────────────────────────
MASTER_IP = "192.168.1.14"   # ← set to master laptop's LAN IP
# ──────────────────────────────────────────────────────────────────────────────

HADOOP_VERSION = "3.3.6"
SPARK_VERSION  = "3.5.1"
JAVA_VERSION   = "11"

OS = platform.system()   # "Darwin" | "Linux" | "Windows"
IS_MAC     = OS == "Darwin"
IS_LINUX   = OS == "Linux"
IS_WINDOWS = OS == "Windows"

# Install root — avoids permission issues on all platforms
if IS_WINDOWS:
    INSTALL_ROOT = Path("C:/hadoop-stack")
else:
    INSTALL_ROOT = Path("/opt")

HADOOP_HOME = Path("/opt/homebrew/Cellar/hadoop/3.5.0/libexec")
SPARK_HOME  = INSTALL_ROOT / f"spark-{SPARK_VERSION}"
DATA_ROOT   = INSTALL_ROOT / "hadoop" / "hdfs"

# Script extensions differ by OS
SBIN_EXT = ".cmd" if IS_WINDOWS else ".sh"

SPARK_MASTER_URL = f"spark://{MASTER_IP}:7077"


def get_local_ip():
    """Reliably get this machine's LAN IP on any platform."""
    # Preferred: connect a UDP socket (doesn't send packets, just resolves route)
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except Exception:
        pass

    # Fallback: platform-specific
    try:
        if IS_WINDOWS:
            out = subprocess.check_output("ipconfig", text=True)
            for line in out.splitlines():
                if "IPv4" in line and "192.168" in line:
                    return line.split(":")[-1].strip()
        elif IS_MAC:
            out = subprocess.check_output(["ipconfig", "getifaddr", "en0"], text=True)
            return out.strip()
        else:
            out = subprocess.check_output(["hostname", "-I"], text=True)
            return out.split()[0]
    except Exception:
        return "127.0.0.1"


def find_java_home():
    """Find JAVA_HOME across macOS, Linux, Windows."""
    # Already set in environment
    if "JAVA_HOME" in os.environ and Path(os.environ["JAVA_HOME"]).exists():
        return Path(os.environ["JAVA_HOME"])

    if IS_WINDOWS:
        # Common Windows JDK locations
        candidates = list(Path("C:/Program Files/Java").glob("jdk-11*")) + \
                     list(Path("C:/Program Files/Eclipse Adoptium").glob("jdk-11*")) + \
                     list(Path("C:/Program Files/Microsoft").glob("jdk-11*"))
        if candidates:
            return candidates[0]

    elif IS_MAC:
        # Homebrew arm64 / x86
        for p in [
            Path("/opt/homebrew/opt/openjdk@11"),
            Path("/usr/local/opt/openjdk@11"),
            Path("/Library/Java/JavaVirtualMachines").glob("*11*/Contents/Home"),
        ]:
            if isinstance(p, Path) and p.exists():
                return p
        # java_home utility
        try:
            out = subprocess.check_output(
                ["/usr/libexec/java_home", "-v", "11"], text=True, stderr=subprocess.DEVNULL
            ).strip()
            if out:
                return Path(out)
        except Exception:
            pass

    else:  # Linux
        for p in [
            Path("/usr/lib/jvm/java-11-openjdk-amd64"),
            Path("/usr/lib/jvm/java-11-openjdk-arm64"),
            Path("/usr/lib/jvm/temurin-11"),
        ]:
            if p.exists():
                return p

    # Last resort: derive from `java` on PATH
    try:
        java_path = subprocess.check_output(
            ["which", "java"] if not IS_WINDOWS else ["where", "java"], text=True
        ).strip().splitlines()[0]
        return Path(java_path).resolve().parent.parent
    except Exception:
        return None


def verify_java():
    """Check Java 11 is available; print install instructions if not."""
    try:
        out = subprocess.check_output(
            ["java", "-version"], stderr=subprocess.STDOUT, text=True
        )
        if "11" in out or "17" in out:   # 17 is also fine
            print(f"  ✓ Java: {out.splitlines()[0]}")
            return True
    except FileNotFoundError:
        pass

    print("  ✗ Java 11 not found. Install it:")
    if IS_MAC:
        print("    brew install openjdk@11")
        print("    Then add to shell: export PATH=$(brew --prefix openjdk@11)/bin:$PATH")
    elif IS_LINUX:
        print("    sudo apt-get install -y openjdk-11-jdk")
    elif IS_WINDOWS:
        print("    Download from: https://adoptium.net  (Java 11, .msi installer)")
        print("    Or: winget install EclipseAdoptium.Temurin.11.JDK")
    return False


if __name__ == "__main__":
    print(f"OS          : {OS}")
    print(f"Local IP    : {get_local_ip()}")
    print(f"MASTER_IP   : {MASTER_IP}")
    print(f"JAVA_HOME   : {find_java_home()}")
    print(f"HADOOP_HOME : {HADOOP_HOME}")
    print(f"SPARK_HOME  : {SPARK_HOME}")
    verify_java()

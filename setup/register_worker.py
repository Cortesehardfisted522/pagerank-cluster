"""
register_worker.py — Run on master to add a worker node to the cluster.
Usage: python3 setup/register_worker.py <worker_ip>
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from config import HADOOP_HOME, SPARK_HOME

def register(ip):
    ip = ip.strip()
    for workers_file in [
        HADOOP_HOME / "etc" / "hadoop" / "workers",
        SPARK_HOME / "conf" / "workers",
    ]:
        if not workers_file.exists():
            print(f"  ⚠  Not found: {workers_file}")
            continue
        existing = workers_file.read_text()
        if ip in existing:
            print(f"  ✓  {ip} already in {workers_file.name}")
        else:
            with open(workers_file, "a") as f:
                f.write(f"{ip}\n")
            print(f"  ✓  Added {ip} → {workers_file}")

    print(f"\n  Worker {ip} registered.")
    print(f"  Restart services for it to take full effect:")
    print(f"    Hadoop: {HADOOP_HOME}/sbin/stop-dfs.sh && {HADOOP_HOME}/sbin/start-dfs.sh")
    print(f"    Spark:  {SPARK_HOME}/sbin/stop-all.sh  && {SPARK_HOME}/sbin/start-all.sh")
    print(f"\n  Or just verify the worker already joined:")
    print(f"    hdfs dfsadmin -report | grep 'Live datanodes'")
    print(f"    curl http://localhost:8080 | grep -c ALIVE")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 setup/register_worker.py <worker_ip>")
        sys.exit(1)
    register(sys.argv[1])

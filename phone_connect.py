#!/usr/bin/env python3
"""
Automated pipeline:
  1. Discover Android device via mDNS (dns-sd)
  2. Connect via ADB over WiFi
  3. Start Appium server (streaming logs)
  4. Run timesheet.py automation
"""

import os
import re
import subprocess
import sys
import threading
import time
import urllib.request
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

APPIUM_HOST = os.environ["APPIUM_HOST"]
APPIUM_PORT = int(os.environ["APPIUM_PORT"])
DEVICE_IP = os.environ["DEVICE_IP"]


class Timeout:
    def __init__(
        self, connect: float = 5.0, read: float = 5.0, total: float | None = None
    ):
        self.connect = connect
        self.read = read
        self.total = total
        self._start = None

    def start(self) -> "Timeout":
        self._start = time.monotonic()
        return self

    def elapsed(self) -> float:
        return time.monotonic() - self._start if self._start is not None else 0.0

    def remaining(self, phase: str = "read") -> float:
        """Return seconds left for the given phase, honouring the total budget."""
        limit = self.connect if phase == "connect" else self.read
        if self.total is not None:
            budget = max(0.0, self.total - self.elapsed())
            return min(limit, budget) if limit is not None else budget
        return limit if limit is not None else 30.0

    def __repr__(self) -> str:
        return (
            f"Timeout(connect={self.connect}, read={self.read}, "
            f"total={self.total}, elapsed={self.elapsed():.1f}s)"
        )


def run(cmd: list[str], timeout_secs: float) -> str:
    """Run a command, capturing stdout. Returns partial output on timeout."""
    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            timeout=timeout_secs,
            text=True,
        )
        return result.stdout
    except subprocess.TimeoutExpired as e:
        return e.stdout.decode() if isinstance(e.stdout, bytes) else (e.stdout or "")


def stream_to_console(proc: subprocess.Popen, prefix: str = "") -> None:
    """Read a process's stdout line-by-line and print with a prefix (runs in a thread)."""
    for line in iter(proc.stdout.readline, ""):
        print(f"{prefix}{line}", end="", flush=True)


def browse_service(t: Timeout) -> str | None:
    print("[ADB] Browsing for _adb-tls-connect._tcp ...")
    output = run(
        ["dns-sd", "-B", "_adb-tls-connect._tcp", "local"], t.remaining("connect")
    )
    for line in output.splitlines():
        if "Add" in line and "_adb-tls-connect" in line:
            service = line.split()[-1]
            print(f"[ADB] Found service: {service}")
            return service
    return None


def lookup_service(service: str, t: Timeout) -> str:
    print(f"[ADB] Resolving {service} ...")
    return run(
        ["dns-sd", "-L", service, "_adb-tls-connect._tcp", "local"], t.remaining("read")
    )


def parse_port(info: str) -> str | None:
    for line in info.splitlines():
        if "can be reached" in line:
            fields = line.split()
            if "at" in fields:
                host_port = fields[fields.index("at") + 1]
                match = re.search(r":(\d+)$", host_port)
                if match:
                    return match.group(1)
    return None


def adb_connect(host: str, port: str) -> bool:
    print(f"[ADB] Connecting to {host}:{port} ...")
    result = subprocess.run(
        ["adb", "connect", f"{host}:{port}"],
        capture_output=True,
        text=True,
    )
    output = result.stdout.strip()
    print(f"[ADB] {output}")
    return "connected" in output


def wait_for_appium(host: str, port: int, timeout_secs: float = 30.0) -> bool:
    """Poll Appium's /status endpoint until it responds or we time out."""
    url = f"http://{host}:{port}/status"
    deadline = time.monotonic() + timeout_secs
    while time.monotonic() < deadline:
        try:
            urllib.request.urlopen(url, timeout=2)
            return True
        except Exception:
            time.sleep(1)
    return False


def start_appium() -> subprocess.Popen | None:
    print(f"[Appium] Starting server on {APPIUM_HOST}:{APPIUM_PORT} ...")
    try:
        proc = subprocess.Popen(
            ["appium", "--address", APPIUM_HOST, "--port", str(APPIUM_PORT)],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
    except FileNotFoundError:
        print("[Appium] ERROR: 'appium' not found. Install with: npm i -g appium")
        return None

    threading.Thread(
        target=stream_to_console, args=(proc, "[Appium] "), daemon=True
    ).start()

    print("[Appium] Waiting for server to be ready ...")
    if not wait_for_appium(APPIUM_HOST, APPIUM_PORT, timeout_secs=30.0):
        print("[Appium] Timed out waiting for server.")
        proc.terminate()
        return None

    print(f"[Appium] Ready at http://{APPIUM_HOST}:{APPIUM_PORT}")
    return proc


def run_timesheet() -> int:
    print("\n[Timesheet] Launching timesheet automation ...")
    result = subprocess.run(
        [sys.executable, "timesheet.py"],
        cwd=Path(__file__).parent,
    )
    return result.returncode


def main():
    t = Timeout(connect=5.0, read=5.0, total=60.0).start()

    service = browse_service(t)
    if not service:
        print("[ADB] No Android device found.")
        sys.exit(1)

    info = lookup_service(service, t)
    if not info.strip():
        print("[ADB] Failed to resolve service info.")
        sys.exit(1)

    port = parse_port(info)
    if not port:
        print("[ADB] Failed to parse port from service info.")
        sys.exit(1)

    if not adb_connect(DEVICE_IP, port):
        print("[ADB] Connection failed.")
        sys.exit(1)

    appium_proc = start_appium()
    if appium_proc is None:
        sys.exit(1)

    rc = run_timesheet()

    print("\n[Appium] Stopping server ...")
    appium_proc.terminate()
    appium_proc.wait()

    print(f"\n{' Done' if rc == 0 else f'✗ Timesheet automation failed (exit {rc})'}")
    sys.exit(rc)


if __name__ == "__main__":
    main()

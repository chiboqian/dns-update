#!/usr/bin/env python3
"""
Update ZoneEdit Dynamic DNS records for one or more hosts.

Credentials: ZoneEdit username and Dynamic DNS token (NOT your account password).

Sources for configuration (precedence high→low):
- CLI flags
- Environment variables: ZONEEDIT_USER, ZONEEDIT_TOKEN, ZONEEDIT_HOSTS (comma list)
- YAML file (default: config/ZoneEdit.yaml) with keys: user, token, hosts: ["host1", "host2"]

Examples:
  # Auto-detect public IPv4 and update a single host
  python util/update_zoneedit_ddns.py --user USER --token TOKEN --host home.example.com

  # Multiple hosts + explicit IP
  python util/update_zoneedit_ddns.py --user USER --token TOKEN \
    --host home.example.com --host nas.example.com --ip 203.0.113.10

  # Using config file and env vars
  export ZONEEDIT_USER=USER
  export ZONEEDIT_TOKEN=TOKEN
  python util/update_zoneedit_ddns.py --config config/ZoneEdit.yaml
"""

import argparse
import os
import sys
from pathlib import Path
from typing import List, Optional, Tuple

import requests
import yaml
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


ZONEEDIT_UPDATE_URL = "https://api.cp.zoneedit.com/dyn/generic.php"


def detect_public_ipv4(timeout: float = 5.0) -> Optional[str]:
    """Detect public IPv4 using several fallback services."""
    endpoints = [
        "https://api.ipify.org",
        "https://ipv4.icanhazip.com",
        "https://ifconfig.me/ip",
    ]
    for url in endpoints:
        try:
            r = requests.get(url, timeout=timeout)
            if r.ok:
                ip = (r.text or "").strip()
                if ip:
                    return ip
        except requests.RequestException:
            continue
    return None


def load_config(path: Optional[str]) -> dict:
    if not path:
        # default path
        cfg = Path(__file__).parent.parent / "config" / "ZoneEdit.yaml"
    else:
        cfg = Path(path)
    if not cfg.exists():
        return {}
    try:
        with open(cfg, "r") as f:
            data = yaml.safe_load(f) or {}
            return data
    except Exception:
        return {}


def resolve_settings(args: argparse.Namespace) -> Tuple[str, str, List[str], str, float, bool]:
    cfg = load_config(args.config)
    user = args.user or os.getenv("ZONEEDIT_USER") or cfg.get("user")
    token = args.token or os.getenv("ZONEEDIT_TOKEN") or cfg.get("token")
    # hosts could be provided as repeated --host or comma list in env/config
    hosts: List[str] = []
    if args.host:
        hosts += args.host
    env_hosts = os.getenv("ZONEEDIT_HOSTS")
    if env_hosts:
        hosts += [h.strip() for h in env_hosts.split(",") if h.strip()]
    cfg_hosts = cfg.get("hosts") or []
    if isinstance(cfg_hosts, list):
        hosts += [str(h).strip() for h in cfg_hosts if str(h).strip()]
    # unique preserve order
    dedup = []
    seen = set()
    for h in hosts:
        if h not in seen:
            dedup.append(h)
            seen.add(h)
    hosts = dedup

    ip = args.ip
    timeout = float(args.timeout or 10.0)
    verbose = bool(args.verbose)

    return user, token, hosts, ip, timeout, verbose


def update_zoneedit_host(user: str, token: str, host: str, ip: str, timeout: float = 10.0) -> Tuple[bool, int, str]:
    """Call ZoneEdit update endpoint for one host.

    Returns (success, status_code, body)
    """
    try:
        params = {"hostname": host, "myip": ip}
        r = requests.get(ZONEEDIT_UPDATE_URL, params=params, auth=(user, token), timeout=timeout)
        ok = r.ok and any(k in r.text.lower() for k in ["ok", "good", "nochg", "updated", "success"])
        return ok, r.status_code, r.text
    except requests.RequestException as e:
        return False, 0, f"request_error: {e}"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Update ZoneEdit Dynamic DNS records", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    p.add_argument("--user", help="ZoneEdit username")
    p.add_argument("--token", help="ZoneEdit dynamic DNS token")
    p.add_argument("--host", action="append", help="Hostname to update (repeat for multiple)")
    p.add_argument("--ip", help="Use this IP instead of auto-detecting")
    p.add_argument("--config", help="Path to YAML config file (default: config/ZoneEdit.yaml)")
    p.add_argument("--timeout", type=float, default=10.0, help="HTTP timeout in seconds")
    p.add_argument("--no-detect", action="store_true", help="Do not auto-detect IP if --ip missing (error instead)")
    p.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    p.add_argument("-q", "--quiet", action="store_true", help="Suppress non-error output")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    user, token, hosts, ip, timeout, verbose = resolve_settings(args)

    # Validate
    if not user or not token:
        print("Error: ZoneEdit user/token required (via CLI, env, or config)", file=sys.stderr)
        return 2
    if not hosts:
        print("Error: at least one --host (or hosts in env/config) is required", file=sys.stderr)
        return 2

    # Resolve IP
    if not ip:
        if args.no_detect:
            print("Error: --ip not provided and --no-detect set", file=sys.stderr)
            return 2
        ip = detect_public_ipv4(timeout=timeout)
        if not ip:
            print("Error: failed to auto-detect public IPv4", file=sys.stderr)
            return 2
        if verbose and not args.quiet:
            print(f"Detected public IP: {ip}")

    successes = 0
    for h in hosts:
        ok, code, body = update_zoneedit_host(user, token, h, ip, timeout=timeout)
        if not args.quiet:
            status = "OK" if ok else "FAIL"
            print(f"[{status}] host={h} ip={ip} http={code} body={body.strip() if isinstance(body, str) else body}")
        if ok:
            successes += 1

    if successes != len(hosts):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

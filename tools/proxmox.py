"""Proxmox tool — queries the M630e for VM/LXC/node status.

Needs an API token: Datacenter > Permissions > API Tokens > Add,
then Datacenter > Permissions > Add > API Token Permission (path /,
role PVEAuditor, propagate on).
"""
import requests
import urllib3

from config import config

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def _headers():
    return {
        "Authorization": f"PVEAPIToken={config.PROXMOX_TOKEN_ID}={config.PROXMOX_TOKEN_SECRET}"
    }


def _get(path: str):
    host = config.PROXMOX_HOST.rstrip("/")
    url = f"{host}/api2/json{path}"
    resp = requests.get(url, headers=_headers(), verify=config.PROXMOX_VERIFY_SSL, timeout=10)
    resp.raise_for_status()
    return resp.json()["data"]


def get_node_status() -> dict:
    data = _get(f"/nodes/{config.PROXMOX_NODE}/status")
    return {
        "cpu_percent": round(data.get("cpu", 0) * 100, 1),
        "memory_used_gb": round(data.get("memory", {}).get("used", 0) / 1e9, 2),
        "memory_total_gb": round(data.get("memory", {}).get("total", 0) / 1e9, 2),
        "uptime_hours": round(data.get("uptime", 0) / 3600, 1),
    }


def list_containers() -> list[dict]:
    data = _get(f"/nodes/{config.PROXMOX_NODE}/lxc")
    return [{"vmid": c["vmid"], "name": c["name"], "status": c["status"]} for c in data]


def list_vms() -> list[dict]:
    data = _get(f"/nodes/{config.PROXMOX_NODE}/qemu")
    return [{"vmid": v["vmid"], "name": v["name"], "status": v["status"]} for v in data]


def get_container_status(name_or_vmid: str) -> dict:
    containers = list_containers()
    for c in containers:
        if str(c["vmid"]) == str(name_or_vmid) or c["name"].lower() == str(name_or_vmid).lower():
            return c
    return {"error": f"No container found matching '{name_or_vmid}'"}

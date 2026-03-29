"""Kodi JSON-RPC helpers."""

import sys
from typing import Optional

import requests

import tvhtokodi
from tvhtokodi import errorNotify

KODI_FILMS_PATH = "/home/chris/seagate4/Films"
KODI_TV_DRAMA_PATH = "/home/chris/seagate4/TV/Drama"
KODI_TV_COMEDY_PATH = "/home/chris/seagate4/TV/Comedy"


class KodiError(Exception):
    """Error raised when Kodi JSON-RPC calls fail."""


def kodi_jsonrpc_url() -> str:
    """Return the configured Kodi JSON-RPC endpoint URL."""
    kodi_host = tvhtokodi.cfg.get("kodiipaddr") or tvhtokodi.cfg.get("sshhost")
    kodi_port = tvhtokodi.cfg.get("kodiport", 8080)
    url = tvhtokodi.cfg.get("kodi_jsonrpc_url")
    if url:
        return url
    if not kodi_host:
        raise KodiError(
            "Missing Kodi host in config (set 'kodiipaddr' or 'kodi_jsonrpc_url')"
        )
    return f"http://{kodi_host}:{kodi_port}/jsonrpc"


def kodi_jsonrpc(method: str, params: Optional[dict] = None) -> dict:
    """Call the Kodi JSON-RPC API and return the decoded payload."""
    try:
        url = kodi_jsonrpc_url()
        user = tvhtokodi.cfg.get("kodiuser")
        password = tvhtokodi.cfg.get("kodipass")
        auth = (user, password) if user and password else None

        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": method,
            "params": params or {},
        }
        response = requests.post(url, json=payload, auth=auth, timeout=30)
        response.raise_for_status()
        data = response.json()

        if "error" in data:
            raise KodiError(str(data["error"]))

        return data
    except Exception as e:
        errorNotify(sys.exc_info()[2], e)
        raise


def scan_kodi_path(path: str, showdialogs: bool = False) -> str:
    """Ask Kodi to scan one directory for new video library items."""
    try:
        if not path:
            raise KodiError("scan path cannot be empty")

        result = kodi_jsonrpc(
            "VideoLibrary.Scan",
            {
                "directory": path,
                "showdialogs": showdialogs,
            },
        )
        return str(result.get("result", "OK"))
    except Exception as e:
        errorNotify(sys.exc_info()[2], e)
        raise


def kodi_scan_path_for_category(category: str) -> str:
    """Return the Kodi scan root that matches the chosen media category."""
    if category == "film":
        return KODI_FILMS_PATH
    if category == "comedy":
        return KODI_TV_COMEDY_PATH
    return KODI_TV_DRAMA_PATH


def test_kodi_connection() -> tuple[bool, str]:
    """Run a lightweight Kodi connectivity/authentication test."""
    try:
        ping = kodi_jsonrpc("JSONRPC.Ping").get("result")
        version = kodi_jsonrpc("JSONRPC.Version").get("result", {}).get("version", {})
        version_str = f"{version.get('major', '?')}.{version.get('minor', '?')}.{version.get('patch', '?')}"
        return True, f"Connected (ping={ping}, api={version_str})"
    except Exception as e:
        return False, str(e)

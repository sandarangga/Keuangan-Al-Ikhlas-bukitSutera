"""
Persist the ledger permanently so transactions entered via the dashboard
survive app restarts/redeploys — not just the current browser session.

Two backends, chosen automatically:

1. GitHub (used automatically when deployed on Streamlit Community Cloud):
   commits the updated ledger straight back to the repo via the GitHub
   Contents API, so the next redeploy (or anyone else's session) picks it
   up. Requires two Secrets to be set in the Streamlit Cloud app:

       GITHUB_TOKEN = "ghp_xxx..."          # a Personal Access Token with 'repo' scope
       GITHUB_REPO  = "username/reponame"   # e.g. "sandarangga/Keuangan-Al-Ikhlas-bukitSutera"

   Optional secrets (sensible defaults are used otherwise):
       GITHUB_BRANCH    = "main"
       GITHUB_FILE_PATH = "data/laporan_keuangan.xlsx"

2. Local file (used automatically when running `streamlit run dashboard.py`
   on your own machine and the GitHub secrets above aren't set): just
   overwrites data/laporan_keuangan.xlsx on disk directly.
"""

from __future__ import annotations

import base64
import json
import os
import urllib.error
import urllib.request
from pathlib import Path


def _secret(name: str, default=None):
    try:
        import streamlit as st

        if name in st.secrets:
            return st.secrets[name]
    except Exception:
        pass
    return os.environ.get(name, default)


def github_configured() -> bool:
    return bool(_secret("GITHUB_TOKEN")) and bool(_secret("GITHUB_REPO"))


def push_to_github(file_bytes: bytes, commit_message: str) -> tuple[bool, str]:
    """Commit `file_bytes` to the configured GitHub repo/path via the
    Contents API. Returns (success, message)."""
    token = _secret("GITHUB_TOKEN")
    repo = _secret("GITHUB_REPO")
    branch = _secret("GITHUB_BRANCH", "main")
    path = _secret("GITHUB_FILE_PATH", "data/laporan_keuangan.xlsx")

    if not token or not repo:
        return False, "GITHUB_TOKEN / GITHUB_REPO belum diatur di Secrets."

    api_url = f"https://api.github.com/repos/{repo}/contents/{path}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "dkm-dashboard-al-ikhlas",
    }

    # GitHub's Contents API requires the current file's blob SHA to update it.
    sha = None
    req = urllib.request.Request(f"{api_url}?ref={branch}", headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            current = json.loads(resp.read())
            sha = current.get("sha")
    except urllib.error.HTTPError as e:
        if e.code != 404:
            return False, f"Gagal cek file di GitHub: {e.code} {e.reason}"
        # 404 is fine: file doesn't exist yet, will be created.
    except Exception as e:
        return False, f"Gagal terhubung ke GitHub: {e}"

    payload = {
        "message": commit_message,
        "content": base64.b64encode(file_bytes).decode("utf-8"),
        "branch": branch,
    }
    if sha:
        payload["sha"] = sha

    req = urllib.request.Request(
        api_url,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="PUT",
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            resp.read()
        return True, "Ledger berhasil disimpan permanen ke GitHub."
    except urllib.error.HTTPError as e:
        try:
            detail = e.read().decode()
        except Exception:
            detail = ""
        return False, f"Gagal commit ke GitHub: {e.code} {e.reason} {detail}"
    except Exception as e:
        return False, f"Gagal terhubung ke GitHub: {e}"


def push_local_file(file_bytes: bytes, local_path) -> tuple[bool, str]:
    try:
        Path(local_path).write_bytes(file_bytes)
        return True, f"Ledger berhasil disimpan ke {local_path} (lokal)."
    except Exception as e:
        return False, f"Gagal menyimpan file lokal: {e}"


def persist_ledger(file_bytes: bytes, local_path, commit_message: str) -> tuple[bool, str, str]:
    """Try GitHub first (works on Streamlit Cloud); fall back to writing the
    local file directly (works when running locally). Returns
    (success, message, method) where method is 'github' or 'local'."""
    if github_configured():
        ok, msg = push_to_github(file_bytes, commit_message)
        return ok, msg, "github"
    ok, msg = push_local_file(file_bytes, local_path)
    return ok, msg, "local"

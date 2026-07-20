"""
Simple password gate for the Kotak Amal input form.

Not all-purpose enterprise auth — this is a lightweight shared-password
check appropriate for a small volunteer team (e.g. bendahara / petugas
penghitung kotak amal) so that not just anyone opening the dashboard can
post new "pemasukan kotak amal" entries.

How to change the password
---------------------------
Option A (recommended): set an environment variable before running Streamlit:

    export KOTAK_AMAL_PASSWORD="password-rahasia-anda"
    streamlit run dashboard.py

Option B: edit DEFAULT_PASSWORD below directly.
"""

import hashlib
import os

DEFAULT_PASSWORD = "amalalikhlas26"


def _hash(pw: str) -> str:
    return hashlib.sha256(pw.encode("utf-8")).hexdigest()


def _current_password_hash() -> str:
    pw = os.environ.get("KOTAK_AMAL_PASSWORD", DEFAULT_PASSWORD)
    return _hash(pw)


def check_password(candidate: str) -> bool:
    if not candidate:
        return False
    return _hash(candidate) == _current_password_hash()

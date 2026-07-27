"""
Simple password gate for the Kotak Amal input form.

Not all-purpose enterprise auth — this is a lightweight shared-password
check appropriate for a small volunteer team (e.g. bendahara / petugas
penghitung kotak amal) so that not just anyone opening the dashboard can
post new "pemasukan kotak amal" entries.

How to change the password
---------------------------
Option A (local): set an environment variable before running Streamlit:

    export KOTAK_AMAL_PASSWORD="password-rahasia-anda"
    streamlit run dashboard.py

Option B (Streamlit Community Cloud): add it to the app's Secrets
(Settings -> Secrets) as:

    KOTAK_AMAL_PASSWORD = "password-rahasia-anda"

Option C: edit DEFAULT_PASSWORD below directly.
"""

import hashlib
import os

DEFAULT_PASSWORD = "amalalikhlas26"


def _hash(pw: str) -> str:
    return hashlib.sha256(pw.encode("utf-8")).hexdigest()


def _configured_password() -> str:
    # 1) Streamlit secrets (used on Streamlit Community Cloud)
    try:
        import streamlit as st

        if "KOTAK_AMAL_PASSWORD" in st.secrets:
            return st.secrets["KOTAK_AMAL_PASSWORD"]
    except Exception:
        pass
    # 2) environment variable (local / other hosts)
    if "KOTAK_AMAL_PASSWORD" in os.environ:
        return os.environ["KOTAK_AMAL_PASSWORD"]
    # 3) fallback default
    return DEFAULT_PASSWORD


def _current_password_hash() -> str:
    return _hash(_configured_password())


def check_password(candidate: str) -> bool:
    if not candidate:
        return False
    return _hash(candidate) == _current_password_hash()

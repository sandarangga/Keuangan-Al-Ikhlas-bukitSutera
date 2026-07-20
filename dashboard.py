"""
Dashboard Keuangan Masjid Al Ikhlas
====================================
Jalankan dengan:
    streamlit run dashboard.py

Secara default dashboard membaca file di data/laporan_keuangan.xlsx.
Admin yang login bisa upload file .xlsx lain, menambah transaksi manual,
dan input hasil hitungan kotak amal.
"""

from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from auth import check_password
from data_loader import (
    append_transaction,
    category_summary,
    load_ledger,
    monthly_summary,
    to_excel_bytes,
)

KOTAK_AMAL_DENOMINASI = [100000, 50000, 20000, 10000, 5000, 2000, 1000, 500]

DEFAULT_PATH = Path(__file__).parent / "data" / "laporan_keuangan.xlsx"

st.set_page_config(
    page_title="Dashboard Keuangan Masjid Al Ikhlas",
    page_icon="🕌",
    layout="wide",
)

# Cegah angka di kartu KPI (st.metric) terpotong "..." saat kolomnya sempit:
# perkecil ukuran font dan matikan ellipsis/overflow-hidden bawaan Streamlit.
st.markdown(
    """
    <style>
    div[data-testid="stMetricValue"] {
        font-size: 1.5rem;
        white-space: normal;
        overflow: visible;
        text-overflow: unset;
        line-height: 1.3;
    }
    div[data-testid="stMetricLabel"] {
        white-space: normal;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def format_rupiah(value: float) -> str:
    return f"Rp {value:,.0f}".replace(",", ".")


@st.cache_data(show_spinner="Membaca data ledger...")
def get_data(file_bytes_or_path):
    return load_ledger(file_bytes_or_path)


if "admin_authed" not in st.session_state:
    st.session_state["admin_authed"] = False


def render_admin_login(location, form_key: str):
    """Render a small login form. `location` is st.sidebar or st (main area).
    Returns True if the login attempt in this run succeeded."""
    with location.form(form_key):
        pw = st.text_input("Password Admin", type="password", key=f"{form_key}_pw")
        submitted = st.form_submit_button("Masuk")
    if submitted:
        if check_password(pw):
            st.session_state["admin_authed"] = True
            st.rerun()
        else:
            location.error("Password salah. Coba lagi.")
    return False


# ---------------------------------------------------------------------------
# Sidebar - login admin, sumber data & navigasi
# ---------------------------------------------------------------------------
st.sidebar.title("🕌 Al Ikhlas")
st.sidebar.caption("Dashboard Keuangan DKM")

st.sidebar.markdown("---")
if st.session_state["admin_authed"]:
    st.sidebar.success("✅ Login sebagai Admin")
    if st.sidebar.button("🚪 Keluar", use_container_width=True):
        st.session_state["admin_authed"] = False
        st.rerun()
else:
    st.sidebar.markdown("**🔒 Login Admin**")
    st.sidebar.caption(
        "Diperlukan untuk ganti file laporan, tambah transaksi, "
        "atau input kotak amal."
    )
    render_admin_login(st.sidebar, "admin_login_sidebar")

st.sidebar.markdown("---")

uploaded = None
if st.session_state["admin_authed"]:
    uploaded = st.sidebar.file_uploader("Ganti file laporan (.xlsx)", type=["xlsx"])

if uploaded is not None:
    source_key = uploaded.name
    base_df = get_data(uploaded)
elif DEFAULT_PATH.exists():
    source_key = str(DEFAULT_PATH)
    base_df = get_data(str(DEFAULT_PATH))
else:
    st.error(
        "File data tidak ditemukan. Login sebagai admin lalu upload file "
        "laporan keuangan (.xlsx) lewat sidebar untuk mulai."
    )
    st.stop()

# Simpan ledger di session_state supaya transaksi baru yang diinput lewat
# form tetap ada selama sesi berjalan (tidak hilang tiap kali dashboard
# me-render ulang). Ganti sumber data -> reset ke ledger asli.
if st.session_state.get("_source_key") != source_key:
    st.session_state["_source_key"] = source_key
    st.session_state["ledger_df"] = base_df.copy()

df = st.session_state["ledger_df"]

st.sidebar.markdown("---")
page = st.sidebar.radio(
    "Halaman", ["📊 Dashboard", "🪙 Input Kotak Amal"], label_visibility="collapsed"
)

# =============================================================================
# HALAMAN: INPUT KOTAK AMAL (dilindungi login admin)
# =============================================================================
if page == "🪙 Input Kotak Amal":
    st.title("🪙 Input Pemasukan Kotak Amal")
    st.caption(
        "Halaman ini khusus untuk petugas penghitung kotak amal / bendahara. "
        "Hasil hitungan akan otomatis tercatat sebagai pemasukan di ledger."
    )

    if not st.session_state["admin_authed"]:
        st.info("🔒 Masukkan password admin untuk mengakses form input kotak amal.")
        render_admin_login(st, "admin_login_kotakamal")
        st.stop()

    st.markdown("---")

    tgl_amal = st.date_input(
        "Tanggal Penghitungan", value=pd.Timestamp.today().date(), key="tgl_amal"
    )
    label_default = f"Kotak Amal {tgl_amal:%d %B %Y}"
    label_amal = st.text_input(
        "Label (opsional, untuk catatan internal — bukan yang dicatat di ledger)",
        value=label_default,
    )

    # Versioned widget keys: incrementing the version after a successful
    # submit gives every number_input a fresh key (defaulting back to 0)
    # without illegally mutating an already-instantiated widget's state.
    if "amal_form_version" not in st.session_state:
        st.session_state["amal_form_version"] = 0
    v = st.session_state["amal_form_version"]

    st.markdown(f"**{label_amal}**")
    header_c1, header_c2, header_c3 = st.columns([2, 2, 2])
    header_c1.markdown("**Pecahan**")
    header_c2.markdown("**Jumlah Lembar/Keping**")
    header_c3.markdown("**Subtotal**")

    total_amal = 0
    for denom in KOTAK_AMAL_DENOMINASI:
        c1, c2, c3 = st.columns([2, 2, 2])
        with c1:
            st.markdown(f"Rp{denom:,.0f}".replace(",", ".") + ",00")
        with c2:
            qty = st.number_input(
                f"jumlah_{denom}",
                min_value=0,
                step=1,
                key=f"amal_qty_{denom}_{v}",
                label_visibility="collapsed",
            )
        subtotal = denom * qty
        total_amal += subtotal
        with c3:
            st.markdown(f"Rp{subtotal:,.0f}".replace(",", "."))

    st.markdown("---")
    st.markdown(f"## Total: Rp{total_amal:,.0f}".replace(",", "."))

    if st.button(
        "✅ Simpan sebagai Pemasukan Kotak Amal",
        type="primary",
        disabled=total_amal <= 0,
        use_container_width=True,
    ):
        st.session_state["ledger_df"] = append_transaction(
            st.session_state["ledger_df"],
            tgl_amal,
            "Pemasukan Kotak Amal",
            "Kotak Amal / Kencleng",
            masuk=total_amal,
            keluar=0,
        )
        st.success(
            f"Tercatat: **Pemasukan Kotak Amal** sebesar "
            f"Rp{total_amal:,.0f}".replace(",", ".")
            + f" pada {tgl_amal:%d %b %Y}."
        )
        st.session_state["amal_form_version"] += 1
        st.rerun()

    st.stop()

# =============================================================================
# HALAMAN: DASHBOARD
# =============================================================================

# -----------------------------------------------------------------------
# Input transaksi baru (khusus admin yang sudah login)
# -----------------------------------------------------------------------
st.sidebar.markdown("---")
st.sidebar.subheader("➕ Tambah Transaksi")
if not st.session_state["admin_authed"]:
    st.sidebar.caption("Login sebagai admin di atas untuk menambah transaksi.")
else:
    with st.sidebar.form("form_tambah_transaksi", clear_on_submit=True):
        tgl_baru = st.date_input("Tanggal", value=df["tanggal"].max().date())
        ket_baru = st.text_input("Keterangan")
        jenis_baru = st.radio("Jenis", ["Pemasukan", "Pengeluaran"], horizontal=True)
        jumlah_baru = st.number_input("Jumlah (Rp)", min_value=0, step=1000, format="%d")
        kategori_opts_all = sorted(df["kategori"].unique().tolist())
        if "Lainnya" not in kategori_opts_all:
            kategori_opts_all.append("Lainnya")
        kategori_baru = st.selectbox(
            "Kategori", kategori_opts_all, index=kategori_opts_all.index("Lainnya")
        )
        submitted = st.form_submit_button("Tambah Transaksi", use_container_width=True)

    if submitted:
        if not ket_baru.strip():
            st.sidebar.error("Keterangan tidak boleh kosong.")
        elif jumlah_baru <= 0:
            st.sidebar.error("Jumlah harus lebih dari 0.")
        else:
            masuk_baru = jumlah_baru if jenis_baru == "Pemasukan" else 0
            keluar_baru = jumlah_baru if jenis_baru == "Pengeluaran" else 0
            st.session_state["ledger_df"] = append_transaction(
                df, tgl_baru, ket_baru, kategori_baru, masuk=masuk_baru, keluar=keluar_baru
            )
            st.sidebar.success(f"Transaksi '{ket_baru}' ditambahkan.")
            st.rerun()

    st.sidebar.caption(
        "Transaksi baru selalu ditambahkan setelah transaksi terakhir & saldo "
        "dilanjutkan dari saldo terkini."
    )

st.sidebar.markdown("---")
st.sidebar.subheader("Filter")

min_date, max_date = df["tanggal"].min().date(), df["tanggal"].max().date()
date_range = st.sidebar.date_input(
    "Rentang tanggal",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date,
)
if isinstance(date_range, tuple) and len(date_range) == 2:
    start_date, end_date = date_range
else:
    start_date, end_date = min_date, max_date

kategori_opts = sorted(df["kategori"].unique())
kategori_sel = st.sidebar.multiselect(
    "Kategori", options=kategori_opts, default=kategori_opts
)

mask = (
    (df["tanggal"].dt.date >= start_date)
    & (df["tanggal"].dt.date <= end_date)
    & (df["kategori"].isin(kategori_sel))
)
fdf = df[mask].copy()

st.sidebar.markdown("---")
st.sidebar.caption(
    f"Data lengkap: {min_date:%d %b %Y} – {max_date:%d %b %Y} · "
    f"{len(df)} transaksi"
)

# ---------------------------------------------------------------------------
# Header & KPI
# ---------------------------------------------------------------------------
st.title("Dashboard Keuangan Masjid Al Ikhlas")
st.caption(
    f"Menampilkan {len(fdf)} transaksi antara "
    f"{start_date:%d %b %Y} – {end_date:%d %b %Y}"
)

saldo_akhir_periode = fdf["saldo"].iloc[-1] if not fdf.empty else 0
saldo_terkini = df["saldo"].iloc[-1]
total_masuk = fdf["masuk"].sum()
total_keluar = fdf["keluar"].sum()
net = total_masuk - total_keluar

c1, c2, c3 = st.columns(3)
c1.metric("Saldo Terkini", format_rupiah(saldo_terkini))
c2.metric("Pemasukan (periode)", format_rupiah(total_masuk))
c3.metric("Pengeluaran (periode)", format_rupiah(total_keluar))

c4, c5 = st.columns(2)
c4.metric(
    "Arus Kas Bersih (periode)",
    format_rupiah(net),
    delta=format_rupiah(net),
    delta_color="normal" if net >= 0 else "inverse",
)
c5.metric("Jumlah Transaksi", f"{len(fdf):,}".replace(",", "."))

st.markdown("---")

# ---------------------------------------------------------------------------
# Transaksi terbesar (ditaruh persis di bawah summary)
# ---------------------------------------------------------------------------
st.subheader("10 Transaksi Terbesar")
top_col1, top_col2 = st.columns(2)

with top_col1:
    st.markdown("**Pemasukan Terbesar**")
    top_in = fdf.nlargest(10, "masuk")[["tanggal", "keterangan", "kategori", "masuk"]]
    st.dataframe(
        top_in.style.format({"tanggal": lambda d: d.strftime("%d %b %Y"), "masuk": "Rp {:,.0f}"}),
        hide_index=True,
        use_container_width=True,
    )

with top_col2:
    st.markdown("**Pengeluaran Terbesar**")
    top_out = fdf.nlargest(10, "keluar")[["tanggal", "keterangan", "kategori", "keluar"]]
    st.dataframe(
        top_out.style.format({"tanggal": lambda d: d.strftime("%d %b %Y"), "keluar": "Rp {:,.0f}"}),
        hide_index=True,
        use_container_width=True,
    )

st.markdown("---")

# ---------------------------------------------------------------------------
# Tren saldo
# ---------------------------------------------------------------------------
st.subheader("Tren Saldo Kas")
saldo_fig = go.Figure()
saldo_fig.add_trace(
    go.Scatter(
        x=fdf["tanggal"],
        y=fdf["saldo"],
        mode="lines",
        fill="tozeroy",
        line=dict(color="#1f8a70", width=2),
        name="Saldo",
        hovertemplate="%{x|%d %b %Y}<br>Saldo: Rp %{y:,.0f}<extra></extra>",
    )
)
saldo_fig.update_layout(
    height=380,
    margin=dict(l=10, r=10, t=10, b=10),
    yaxis_title="Saldo (Rp)",
    xaxis_title=None,
    hovermode="x unified",
)
st.plotly_chart(saldo_fig, use_container_width=True)

# ---------------------------------------------------------------------------
# Pemasukan vs Pengeluaran per bulan
# ---------------------------------------------------------------------------
st.subheader("Pemasukan vs Pengeluaran per Bulan")
msum = monthly_summary(fdf)

bar_fig = go.Figure()
bar_fig.add_bar(
    x=msum["bulan"], y=msum["masuk"], name="Pemasukan", marker_color="#2e8b57"
)
bar_fig.add_bar(
    x=msum["bulan"], y=msum["keluar"], name="Pengeluaran", marker_color="#c0392b"
)
bar_fig.add_trace(
    go.Scatter(
        x=msum["bulan"],
        y=msum["net"],
        name="Arus Kas Bersih",
        mode="lines+markers",
        line=dict(color="#2c3e50", width=2, dash="dot"),
        yaxis="y",
    )
)
bar_fig.update_layout(
    barmode="group",
    height=400,
    margin=dict(l=10, r=10, t=10, b=10),
    yaxis_title="Rupiah",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
)
st.plotly_chart(bar_fig, use_container_width=True)

# ---------------------------------------------------------------------------
# Breakdown kategori
# ---------------------------------------------------------------------------
st.subheader("Breakdown per Kategori")
col_masuk, col_keluar = st.columns(2)

with col_masuk:
    st.markdown("**Sumber Pemasukan**")
    cat_masuk = category_summary(fdf, "masuk")
    if cat_masuk.empty:
        st.info("Tidak ada data pemasukan pada periode ini.")
    else:
        fig = px.pie(
            cat_masuk, names="kategori", values="total", hole=0.45,
            color_discrete_sequence=px.colors.sequential.Greens_r,
        )
        fig.update_traces(textposition="inside", textinfo="percent+label")
        fig.update_layout(height=380, margin=dict(l=10, r=10, t=10, b=10), showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

with col_keluar:
    st.markdown("**Kategori Pengeluaran**")
    cat_keluar = category_summary(fdf, "keluar")
    if cat_keluar.empty:
        st.info("Tidak ada data pengeluaran pada periode ini.")
    else:
        fig = px.pie(
            cat_keluar, names="kategori", values="total", hole=0.45,
            color_discrete_sequence=px.colors.sequential.Reds_r,
        )
        fig.update_traces(textposition="inside", textinfo="percent+label")
        fig.update_layout(height=380, margin=dict(l=10, r=10, t=10, b=10), showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

# ---------------------------------------------------------------------------
# Tabel transaksi lengkap
# ---------------------------------------------------------------------------
st.markdown("---")
st.subheader("Daftar Transaksi")

search = st.text_input("Cari keterangan...", "")
table_df = fdf.copy()
if search:
    table_df = table_df[table_df["keterangan"].str.contains(search, case=False, na=False)]

display_df = table_df[["tanggal", "keterangan", "kategori", "masuk", "keluar", "saldo"]].sort_values(
    "tanggal", ascending=False
)
st.dataframe(
    display_df.style.format(
        {
            "tanggal": lambda d: d.strftime("%d %b %Y"),
            "masuk": "Rp {:,.0f}",
            "keluar": "Rp {:,.0f}",
            "saldo": "Rp {:,.0f}",
        }
    ),
    hide_index=True,
    use_container_width=True,
    height=400,
)

dl_col1, dl_col2, dl_col3 = st.columns([1, 1, 2])
with dl_col1:
    csv = display_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇️ Unduh terfilter (CSV)", csv, "transaksi_al_ikhlas.csv", "text/csv",
        use_container_width=True,
    )
with dl_col2:
    xlsx_filtered = to_excel_bytes(table_df.sort_values("tanggal"))
    st.download_button(
        "⬇️ Unduh terfilter (XLSX)",
        xlsx_filtered,
        "transaksi_al_ikhlas_terfilter.xlsx",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )
with dl_col3:
    xlsx_full = to_excel_bytes(df.sort_values("tanggal"))
    st.download_button(
        "⬇️ Unduh SELURUH ledger (XLSX) — termasuk transaksi baru",
        xlsx_full,
        "ledger_al_ikhlas_lengkap.xlsx",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )

st.caption(
    "Sumber: Laporan Keuangan Al Ikhlas — Sheet1 (ledger transaksi). "
    "Transaksi yang ditambahkan lewat form berlaku untuk sesi ini; "
    "gunakan tombol unduh XLSX untuk menyimpannya secara permanen."
)

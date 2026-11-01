"""
Dashboard kondisi parkiran motor (Streamlit)

Jalankan:
    pip install streamlit pandas
    streamlit run dashboard_parkiran.py

Input: hasil_v3.csv dengan kolom minimal:
    sesi, row, titik, kapasitas, motor_depan_v3
(kolom slot_kosong dan status akan dihitung ulang di sini)

Letakkan hasil_v3.csv di folder yang sama, atau ubah CSV_PATH di bawah,
atau upload lewat sidebar.
"""

import os
from datetime import datetime
from zoneinfo import ZoneInfo

import pandas as pd
import streamlit as st

# ----------------------------------------------------------------- konfigurasi
CSV_PATH = "hasil_v3.csv"
TZ = ZoneInfo("Asia/Jakarta")           # ganti kalau perlu, mis. "Asia/Makassar"

st.set_page_config(page_title="Kondisi Parkiran Motor", page_icon="🏍️", layout="wide")

# ----------------------------------------------------------------------- gaya
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap');

html, body, [class*="css"], .stApp, button, input, select, textarea {
    font-family: 'Poppins', sans-serif !important;
}
.block-container { padding-top: 2rem; max-width: 1250px; }

.judul { font-size: 1.9rem; font-weight: 700; margin: 0; }
.update {
    display: inline-block; margin-top: 6px; padding: 6px 14px;
    border-radius: 999px; background: #eef1f5; color: #333;
    font-size: .85rem; font-weight: 500;
}
.update b { font-weight: 600; }

.ringkas { display: flex; gap: 14px; flex-wrap: wrap; margin: 18px 0 6px; }
.ringkas .k {
    flex: 1; min-width: 160px; padding: 14px 18px; border-radius: 12px;
    background: #fff; border: 1px solid #e3e6ea;
}
.ringkas .k .v { font-size: 1.7rem; font-weight: 700; line-height: 1.2; }
.ringkas .k .l { font-size: .8rem; color: #666; }

.legend { display: flex; gap: 18px; flex-wrap: wrap; font-size: .82rem; color: #444; margin: 8px 0 18px; }
.legend span i {
    display: inline-block; width: 12px; height: 12px; border-radius: 3px;
    margin-right: 6px; vertical-align: -1px;
}

.tabel-wrap { overflow-x: auto; background: #fff; border: 1px solid #e3e6ea; border-radius: 14px; padding: 8px; }
table.grid { border-collapse: separate; border-spacing: 6px; width: 100%; }
table.grid th {
    font-weight: 600; font-size: .85rem; color: #333; padding: 6px 4px; text-align: center;
}
table.grid th.rowname { text-align: left; padding-left: 8px; white-space: nowrap; }
table.grid td { text-align: center; border-radius: 10px; padding: 10px 8px; min-width: 84px; color: #1d1d1d; }
table.grid td .n { font-size: 1.5rem; font-weight: 700; line-height: 1.1; }
table.grid td .s { font-size: .7rem; opacity: .8; }
table.grid td.total { background: #eef1f5; }
table.grid td.penuh    { background: #f4b6b6; }
table.grid td.sebagian { background: #fde8a8; }
table.grid td.banyak   { background: #b8e6b8; }
table.grid td.kosongdata { background: #f0f0f0; color: #888; }

.catatan { font-size: .78rem; color: #666; margin-top: 4px; }

</style>
""",
    unsafe_allow_html=True,
)


# ----------------------------------------------------------------------- data
def status_slot(kapasitas: int, terisi: int) -> str:
    """Sama dengan logika sebelumnya: penuh / sebagian / banyak kosong."""
    kosong = max(kapasitas - terisi, 0)
    if terisi >= kapasitas or kosong <= 1:
        return "penuh"
    if kosong / kapasitas >= 0.5:
        return "banyak"
    return "sebagian"


@st.cache_data(show_spinner=False)
def muat_csv(sumber, kunci_cache):
    df = pd.read_csv(sumber)
    df.columns = df.columns.str.strip()
    df["sesi"] = df["sesi"].str.upper()
    df["row"] = df["row"].str.upper()
    df["titik"] = df["titik"].astype(str).str.upper()
    df["kapasitas"] = df["kapasitas"].astype(int)
    df["terisi"] = df["motor_depan_v3"].astype(int)
    df["slot_kosong"] = (df["kapasitas"] - df["terisi"]).clip(lower=0)
    df["status"] = [status_slot(k, t) for k, t in zip(df["kapasitas"], df["terisi"])]
    return df


with st.sidebar:
    st.markdown("### Sumber data")
    upload = st.file_uploader("Upload hasil_v3.csv", type="csv")
    st.caption(f"Tanpa upload, dibaca dari `{CSV_PATH}`.")
    if st.button("Muat ulang data"):
        st.cache_data.clear()
        st.rerun()

if upload is not None:
    df = muat_csv(upload, upload.name + str(upload.size))
    waktu_data = datetime.now(TZ)
    asal = f"upload {upload.name}"
elif os.path.exists(CSV_PATH):
    mtime = os.path.getmtime(CSV_PATH)
    df = muat_csv(CSV_PATH, mtime)
    waktu_data = datetime.fromtimestamp(mtime, TZ)
    asal = CSV_PATH
else:
    st.error(
        f"File `{CSV_PATH}` tidak ditemukan. Letakkan di folder yang sama dengan "
        "dashboard ini, atau upload lewat sidebar."
    )
    st.stop()

# -------------------------------------------------------------------- header
st.markdown('<p class="judul">Kondisi Parkiran Motor</p>', unsafe_allow_html=True)
st.markdown(
    f'<span class="update">Data diperbarui: <b>{waktu_data.strftime("%d %b %Y, %H:%M")} '
    f'{waktu_data.tzname()}</b> &nbsp;|&nbsp; sumber: {asal}</span>',
    unsafe_allow_html=True,
)

sesi_ada = [s for s in ["PAGI", "MALAM"] if s in df["sesi"].unique()]
tabs = st.tabs([s.capitalize() for s in sesi_ada])


def render_sesi(sesi: str):
    sub = df[df["sesi"] == sesi]
    total_kosong = int(sub["slot_kosong"].sum())
    total_kap = int(sub["kapasitas"].sum())
    total_isi = int(sub["terisi"].sum())
    okupansi = 100 * total_isi / total_kap if total_kap else 0
    n_penuh = int((sub["status"] == "penuh").sum())

    st.markdown(
        f"""
<div class="ringkas">
<div class="k"><div class="v">{total_kosong}</div><div class="l">slot kosong dari {total_kap}</div></div>
<div class="k"><div class="v">{okupansi:.0f}%</div><div class="l">okupansi</div></div>
<div class="k"><div class="v">{n_penuh}/{len(sub)}</div><div class="l">blok berstatus penuh</div></div>
</div>
<div class="legend">
<span><i style="background:#f4b6b6"></i>Penuh (kosong 0-1)</span>
<span><i style="background:#fde8a8"></i>Sebagian kosong</span>
<span><i style="background:#b8e6b8"></i>Banyak kosong (&ge; 50% kapasitas)</span>
</div>
""",
        unsafe_allow_html=True,
    )

    rows = sorted(sub["row"].unique(), key=lambda r: int("".join(c for c in r if c.isdigit()) or 0))
    cols = sorted(sub["titik"].unique())

    h = '<div class="tabel-wrap"><table class="grid"><tr><th></th>'
    h += "".join(f"<th>Blok {c}</th>" for c in cols) + "<th>Total ROW</th></tr>"
    for r in rows:
        sr = sub[sub["row"] == r]
        peta = {t: x for t, x in zip(sr["titik"], sr.itertuples())}
        h += f'<tr><th class="rowname">{r}</th>'
        for c in cols:
            x = peta.get(c)
            if x is None:
                h += '<td class="kosongdata">-</td>'
            else:
                h += (f'<td class="{x.status}"><div class="n">{x.slot_kosong}</div>'
                      f'<div class="s">{x.terisi}/{x.kapasitas} terisi</div></td>')
        rk, rc = int(sr["slot_kosong"].sum()), int(sr["kapasitas"].sum())
        h += f'<td class="total"><div class="n">{rk}</div><div class="s">dari {rc} slot</div></td></tr>'
    h += "</table></div>"
    st.markdown(h, unsafe_allow_html=True)

    st.markdown(
        '<p class="catatan">Angka besar = estimasi slot kosong (akurasi sekitar &plusmn;1 motor per blok). '
        "Blok padat di malam hari bisa terhitung lebih kosong dari kenyataan.</p>",
        unsafe_allow_html=True,
    )


for tab, sesi in zip(tabs, sesi_ada):
    with tab:
        render_sesi(sesi)

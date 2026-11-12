"""
Dashboard Biaya Asuransi Kesehatan - Statistika dan Probabilitas 1 (Kelas A)

Jalankan dari terminal (di dalam folder ini):
    streamlit run dashboard.py
"""
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st

# ======================================================================
# 1. KONFIGURASI HALAMAN
# ======================================================================
st.set_page_config(page_title="Dashboard Asuransi", page_icon="💜", layout="wide")

DATA_PATH = Path(__file__).parent / "data.csv"
UNGU, ORANYE = "#7C3AED", "#FB923C"
NAMA_PEROKOK = {"yes": "Perokok", "no": "Bukan perokok"}
WARNA_PEROKOK = {"yes": UNGU, "no": ORANYE}


# ======================================================================
# 2. FUNGSI BANTU
# ======================================================================
@st.cache_data          # data dibaca sekali saja, bukan setiap interaksi
def muat_data(path):
    df = pd.read_csv(path)
    df = df.drop_duplicates().dropna()          # wrangling: buang duplikat dan data kosong
    bawah = (df["age"] // 10) * 10              # kelompok usia per 10 tahun
    df["kelompok_usia"] = bawah.astype(str) + "-" + (bawah + 9).astype(str)
    return df


def hitung_statistik(x: pd.Series) -> dict:
    """Hitung ukuran statistik deskriptif untuk satu kolom."""
    q1, q3 = x.quantile(0.25), x.quantile(0.75)
    iqr = q3 - q1
    batas_bawah = q1 - 1.5 * iqr
    batas_atas = q3 + 1.5 * iqr
    return {
        "n": len(x),
        "mean": x.mean(),
        "median": x.median(),
        "modus": list(x.mode()),
        "std": x.std(),
        "min": x.min(),
        "max": x.max(),
        "q1": q1,
        "q3": q3,
        "iqr": iqr,
        "batas_bawah": batas_bawah,
        "batas_atas": batas_atas,
        "outlier": x[(x < batas_bawah) | (x > batas_atas)],
    }


def format_modus(daftar, maks_tampil=3):
    teks = ", ".join(f"{m:g}" for m in daftar[:maks_tampil])
    return teks + (" ..." if len(daftar) > maks_tampil else "")


df = muat_data(DATA_PATH)
kolom_numerik = ["age", "bmi", "children", "charges"]
kolom_kategori = ["sex", "smoker", "region"]

# ======================================================================
# 3. SIDEBAR: FILTER
# ======================================================================
st.sidebar.title("💜 MediCost")
st.sidebar.caption("Analisis Biaya Asuransi Kesehatan")

st.sidebar.subheader("Filter data")
df_f = df.copy()
for k in kolom_kategori:
    semua = sorted(df[k].unique())
    pilihan = st.sidebar.multiselect(k, semua, default=semua)
    df_f = df_f[df_f[k].isin(pilihan)]

usia = st.sidebar.slider("Rentang usia", int(df["age"].min()), int(df["age"].max()),
                         (int(df["age"].min()), int(df["age"].max())))
bmi = st.sidebar.slider("Rentang BMI", float(df["bmi"].min()), float(df["bmi"].max()),
                        (float(df["bmi"].min()), float(df["bmi"].max())))
df_f = df_f[(df_f["age"] >= usia[0]) & (df_f["age"] <= usia[1])]
df_f = df_f[(df_f["bmi"] >= bmi[0]) & (df_f["bmi"] <= bmi[1])]

if df_f.empty:
    st.warning("Tidak ada data setelah difilter. Longgarkan filter di sidebar.")
    st.stop()

# ======================================================================
# 4. HALAMAN UTAMA
# ======================================================================
st.title("💜 Dashboard Biaya Asuransi Kesehatan")
st.caption(f"Data terpilih: {len(df_f)} dari {len(df)} baris")
st.info(
    "**Pertanyaan analisis:** (1) Faktor apa (perokok, usia, BMI) yang paling memengaruhi biaya asuransi? "
    "(2) Apakah ada perbedaan rata-rata biaya antar wilayah dan jenis kelamin?"
)

# ---------- Ringkasan angka ----------
k1, k2, k3, k4 = st.columns(4)
k1.metric("Total Peserta", f"{len(df_f):,}")
k2.metric("Rata-rata Biaya", f"${df_f['charges'].mean():,.0f}")
k3.metric("Biaya Tertinggi", f"${df_f['charges'].max():,.0f}")
k4.metric("Persentase Perokok", f"{(df_f['smoker'] == 'yes').mean() * 100:.1f}%")

tab_ringkas, tab_vis, tab_stat, tab_data = st.tabs(
    ["🏠 Ringkasan", "📈 Visualisasi", "🧮 Statistik", "📋 Data"]
)

# ----------------------------- TAB RINGKASAN --------------------------
with tab_ringkas:
    kiri, kanan = st.columns([2, 1])

    with kiri:
        st.subheader("Rata-rata Biaya per Kelompok Usia")
        tabel = df_f.groupby(["kelompok_usia", "smoker"])["charges"].mean().unstack()
        posisi = np.arange(len(tabel))
        lebar = 0.4
        fig, ax = plt.subplots(figsize=(7, 3.5))
        for i, s in enumerate(tabel.columns):
            ax.bar(posisi + i * lebar, tabel[s], width=lebar, color=WARNA_PEROKOK[s], label=NAMA_PEROKOK[s])
        ax.set_xticks(posisi + lebar / 2)
        ax.set_xticklabels(tabel.index)
        ax.set_xlabel("Kelompok usia (tahun)")
        ax.set_ylabel("Rata-rata biaya (USD)")
        ax.set_title("Biaya Asuransi per Kelompok Usia")
        ax.legend()
        st.pyplot(fig)
        st.caption("Biaya naik seiring usia, tetapi batang perokok selalu jauh lebih tinggi. "
                   "Artinya status merokok berpengaruh lebih besar daripada usia.")

    with kanan:
        st.subheader("Komposisi Peserta")
        pilih = st.selectbox("Tampilkan berdasarkan", ["sex", "smoker", "region"])
        jumlah = df_f.groupby(pilih)["charges"].count()
        fig, ax = plt.subplots(figsize=(4, 3.5))
        ax.bar(jumlah.index, jumlah.values, color=UNGU)
        ax.set_xlabel(pilih)
        ax.set_ylabel("Jumlah peserta")
        ax.set_title(f"Jumlah Peserta per {pilih}")
        st.pyplot(fig)
        st.caption(f"Kelompok terbanyak: {jumlah.sort_values(ascending=False).index[0]}.")

    kiri2, kanan2 = st.columns([2, 1])

    with kiri2:
        st.subheader("10 Peserta dengan Biaya Tertinggi")
        top10 = df_f.sort_values("charges", ascending=False).head(10)
        st.dataframe(top10[["age", "sex", "bmi", "smoker", "region", "charges"]], hide_index=True)
        st.caption("Hampir semua biaya teratas berasal dari perokok dengan BMI tinggi.")

    with kanan2:
        st.subheader("Insight Utama")
        g_rokok = df_f.groupby("smoker")["charges"].mean()
        if "yes" in g_rokok.index and "no" in g_rokok.index:
            st.info(f"🚬 Biaya perokok {g_rokok['yes'] / g_rokok['no']:.1f}x lipat bukan perokok.")
        g_usia = df_f.groupby("kelompok_usia")["charges"].mean().sort_values(ascending=False)
        st.info(f"🎂 Usia termahal: {g_usia.index[0]} tahun (rata-rata ${g_usia.iloc[0]:,.0f}).")
        g_wil = df_f.groupby("region")["charges"].mean().sort_values(ascending=False)
        st.info(f"📍 Wilayah tertinggi: {g_wil.index[0]} (rata-rata ${g_wil.iloc[0]:,.0f}).")

# --------------------------- TAB VISUALISASI --------------------------
with tab_vis:
    stat = hitung_statistik(df_f["charges"])
    a, b = st.columns(2)

    with a:
        st.subheader("Histogram Biaya")
        n_bins = st.slider("Jumlah bin", 5, 40, 20)
        fig, ax = plt.subplots(figsize=(6, 4))
        ax.hist(df_f["charges"], bins=n_bins, edgecolor="black", color=UNGU)
        ax.axvline(stat["mean"], color="red", linestyle="--", label=f"Mean = {stat['mean']:,.0f}")
        ax.axvline(stat["median"], color="green", label=f"Median = {stat['median']:,.0f}")
        ax.set_xlabel("Biaya (USD)")
        ax.set_ylabel("Frekuensi")
        ax.set_title("Distribusi Biaya Asuransi")
        ax.legend()
        st.pyplot(fig)
        st.caption("Mean lebih besar dari median, jadi distribusi condong ke kanan: "
                   "kebanyakan biaya rendah, sedikit orang berbiaya sangat tinggi.")

    with b:
        st.subheader("Boxplot Biaya per Status Perokok")
        label, data = [], []
        for nama_grup, isi in df_f.groupby("smoker"):
            label.append(NAMA_PEROKOK[nama_grup])
            data.append(isi["charges"])
        fig, ax = plt.subplots(figsize=(6, 4))
        ax.boxplot(data)
        ax.set_xticks(range(1, len(label) + 1))
        ax.set_xticklabels(label)
        ax.set_xlabel("Status perokok")
        ax.set_ylabel("Biaya (USD)")
        ax.set_title("Sebaran Biaya per Status Perokok")
        st.pyplot(fig)
        st.caption("Median dan kotak perokok jauh di atas bukan perokok, dan rentangnya lebih lebar.")

    c, d = st.columns(2)

    with c:
        st.subheader("Rata-rata Biaya per Usia")
        st.line_chart(df_f.groupby("age")["charges"].mean())
        st.caption("Garis naik seiring bertambahnya usia (sumbu x: usia, sumbu y: rata-rata biaya USD).")

    with d:
        st.subheader("BMI vs Biaya")
        fig, ax = plt.subplots(figsize=(6, 4))
        for nama_grup, isi in df_f.groupby("smoker"):
            ax.scatter(isi["bmi"], isi["charges"], alpha=0.6,
                       color=WARNA_PEROKOK[nama_grup], label=NAMA_PEROKOK[nama_grup])
        ax.set_xlabel("BMI")
        ax.set_ylabel("Biaya (USD)")
        ax.set_title("Hubungan BMI dan Biaya")
        ax.legend()
        st.pyplot(fig)
        r = df_f["bmi"].corr(df_f["charges"])
        st.caption(f"Korelasi BMI-biaya r = {r:.2f} (lemah), tetapi pada perokok dengan BMI di atas 30 biaya melonjak.")

    st.subheader("Rata-rata Biaya per Wilayah")
    rata_wil = df_f.groupby("region")["charges"].mean()
    fig, ax = plt.subplots(figsize=(8, 3.5))
    ax.bar(rata_wil.index, rata_wil.values, color=UNGU)
    ax.set_xlabel("Wilayah")
    ax.set_ylabel("Rata-rata biaya (USD)")
    ax.set_title("Rata-rata Biaya Asuransi per Wilayah")
    st.pyplot(fig)
    st.caption("Selisih antar wilayah kecil dibanding selisih perokok vs bukan perokok, "
               "jadi wilayah bukan faktor utama biaya.")

# --------------------------- TAB STATISTIK ----------------------------
with tab_stat:
    kolom = st.selectbox("Kolom yang dianalisis", kolom_numerik, index=3)
    stat = hitung_statistik(df_f[kolom])

    st.subheader("Ukuran Pemusatan")
    a, b, c, d = st.columns(4)
    a.metric("Mean", f"{stat['mean']:.2f}")
    b.metric("Median", f"{stat['median']:.2f}")
    c.metric("Modus", format_modus(stat["modus"]))
    d.metric("Jumlah data (n)", stat["n"])

    st.subheader("Ukuran Penyebaran")
    e, f, g, h = st.columns(4)
    e.metric("Std Dev (sampel)", f"{stat['std']:.2f}")
    f.metric("Range", f"{stat['max'] - stat['min']:.2f}")
    g.metric("IQR", f"{stat['iqr']:.2f}")
    h.metric("Jumlah outlier", len(stat["outlier"]))

    selisih = stat["mean"] - stat["median"]
    if abs(selisih) < 0.1 * stat["std"]:
        st.success("Mean ≈ Median → distribusi relatif **simetris**.")
    elif selisih > 0:
        st.info("Mean > Median → distribusi **condong ke kanan** (ada nilai besar yang menarik mean).")
    else:
        st.info("Mean < Median → distribusi **condong ke kiri** (ada nilai kecil yang menarik mean).")

    with st.expander("Detail kuartil dan batas outlier (aturan 1,5 × IQR)"):
        st.write(f"Q1 = {stat['q1']:.2f} | Q3 = {stat['q3']:.2f}")
        st.write(f"Batas bawah = {stat['batas_bawah']:.2f} | Batas atas = {stat['batas_atas']:.2f}")

    st.subheader("Ringkasan semua kolom numerik")
    st.dataframe(df_f[kolom_numerik].describe().round(2))

    st.subheader("Korelasi antar kolom numerik")
    st.dataframe(df_f[kolom_numerik].corr().round(2))
    st.caption("Mendekati 1 berarti hubungan positif kuat. Usia paling berkorelasi dengan biaya; jumlah anak hampir tidak.")

# ----------------------------- TAB DATA -------------------------------
with tab_data:
    c1, c2, c3 = st.columns(3)
    c1.metric("Jumlah baris", len(df_f))
    c2.metric("Jumlah kolom", df_f.shape[1])
    c3.metric("Data kosong (total)", int(df_f.isna().sum().sum()))
    st.dataframe(df_f)

st.divider()
st.caption("Sumber data: Medical Cost Personal Datasets (Kaggle). Statistika dan Probabilitas 1 - Kelas A")

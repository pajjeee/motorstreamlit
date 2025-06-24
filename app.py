# -------------------------------------------------------------------
# 1. IMPOR LIBRARY YANG DIBUTUHKAN
# -------------------------------------------------------------------
import streamlit as st
import datetime
import time
import joblib
import pandas as pd
import numpy as np

# -------------------------------------------------------------------
# 2. KONFIGURASI HALAMAN DAN TAMPILAN (CSS)
# -------------------------------------------------------------------
st.set_page_config(
    page_title="Prediksi Harga Motor Bekas",
    page_icon="🏍️",
    layout="wide"
)

# URL gambar online untuk latar belakang
image_url = "https://images.pexels.com/photos/3137072/pexels-photo-3137072.jpeg"

# CSS Kustom dengan latar belakang gambar online
st.markdown(f"""
<style>
.stApp {{
    background-image: url("{image_url}");
    background-size: cover;
    background-repeat: no-repeat;
    background-attachment: fixed;
}}

/* Membuat kontainer utama sedikit transparan agar teks lebih mudah dibaca */
.main .block-container {{
    background-color: rgba(0, 0, 0, 0.6); /* Hitam dengan 60% transparansi */
    padding: 2rem;
    border-radius: 10px;
}}

/* Mengubah warna teks agar kontras dengan background gelap */
h1, h2, h3, p, label, .stMarkdown {{
    color: white !important;
}}

/* Style untuk tombol */
.stButton>button {{
    background-color: #4A4AFF;
    color: white;
    border: none;
    font-weight: bold;
}}
.stButton>button:hover {{
    background-color: #3535d6;
}}

/* Style untuk input dan dropdown agar terlihat jelas */
.stTextInput>div>div>input, .stNumberInput>div>div>input, .stSelectbox>div>div {{
    background-color: rgba(255, 255, 255, 0.9);
    color: black !important;
    border-radius: 5px;
}}
.stSelectbox>div>div>div>div {{
    color: black !important;
}}

</style>
""", unsafe_allow_html=True)


# -------------------------------------------------------------------
# "KAMUS" OTOMATIS DARI FILE CSV DAN MAPPING MANUAL
# -------------------------------------------------------------------
# Membaca mapping model motor dari file CSV secara otomatis
try:
    mapping_df = pd.read_csv('model_mapping.csv')
    # Membuat kamus dari DataFrame: {"Nama Model": KodeAngka}
    model_mapping = pd.Series(mapping_df.kode_model.values, index=mapping_df.nama_model).to_dict()
except FileNotFoundError:
    st.error("File 'model_mapping.csv' tidak ditemukan! Aplikasi tidak bisa menampilkan pilihan model motor.")
    # Fallback jika file tidak ada, agar aplikasi tidak crash
    model_mapping = {"Harap buat file model_mapping.csv": 0}

# Mapping untuk kisaran CC ke nilai tengahnya
cc_mapping = {
    "Di bawah 100 CC": 80,
    "100 - 150 CC": 125,
    "151 - 250 CC": 200,
    "251 - 500 CC": 375,
    "Di atas 500 CC": 600
}

fuel_mapping = {
    "Gasoline (Bensin)": 3, "Diesel": 2, "Electric (Listrik)": 5, "LPG": 1,
    "Electric/Gasoline (Hybrid)": 4, "Two Stroke Gasoline (Bensin 2-Tak)": 6, "Others (Lainnya)": 7
}

gear_mapping = { "Manual": 1, "Otomatis": 2, "Semi-Otomatis": 3 }


# -------------------------------------------------------------------
# 3. TAMPILAN UTAMA APLIKASI (JUDUL DAN FORM INPUT)
# -------------------------------------------------------------------
st.title("Prediksi Harga Motor Bekas")
st.markdown("<p style='text-align: center; color:white;'>Pilih spesifikasi motor untuk mengetahui estimasi harganya.</p>", unsafe_allow_html=True)

with st.form(key="prediction_form"):
    st.header("Detail Kendaraan")

    # Baris 1: Input numerik biasa
    col1, col2, col3 = st.columns(3)
    with col1:
        # PENGGUNA MEMILIH KISARAN CC
        power_cc_range = st.selectbox("Pilih Kisaran Tenaga (CC)", options=list(cc_mapping.keys()))
    with col2:
        mileage = st.number_input("Jarak Tempuh (km)", min_value=0.0, value=132.0, format="%.1f")
    with col3:
        date = st.number_input("Tahun Registrasi", min_value=1990, max_value=datetime.datetime.now().year, value=2020)
    
    st.write("") # Spasi
    
    # Baris 2: Input dropdown yang otomatis terisi dari file CSV
    col4, col5, col6 = st.columns(3)
    with col4:
        make_model_text = st.selectbox(
            "Cari & Pilih Model Motor",
            options=list(model_mapping.keys()),
            help="Klik di dalam kotak ini dan ketik nama motor untuk mencari dengan mudah."
        )
    with col5:
        fuel_text = st.selectbox("Pilih Jenis Bahan Bakar", options=list(fuel_mapping.keys()))
    with col6:
        gear_text = st.selectbox("Pilih Jenis Transmisi", options=list(gear_mapping.keys()))

    st.write("")
    submit_button = st.form_submit_button(label="✨ Prediksi Harga!")

# -------------------------------------------------------------------
# 4. PROSES SETELAH TOMBOL PREDIKSI DITEKAN
# -------------------------------------------------------------------
if submit_button:
    try:
        # --- Proses Penerjemahan & Konversi Otomatis ---
        make_model_code = model_mapping[make_model_text]
        fuel_code = fuel_mapping[fuel_text]
        gear_code = gear_mapping[gear_text]
        
        # Mengambil nilai tengah CC dari kisaran yang dipilih
        power_cc_value = cc_mapping[power_cc_range]
        # Mengkonversi nilai tengah CC ke HP untuk model
        power_hp = power_cc_value / 16.0

        # Memuat model
        model = joblib.load('motormodel.sav')
        
        # Menyiapkan data untuk dikirim ke model
        kolom_model = ['mileage', 'power', 'make_model', 'date', 'fuel', 'gear']
        input_data = pd.DataFrame({
            'mileage': [mileage],
            'power': [power_hp], # Menggunakan power dalam HP yang sudah dikonversi
            'make_model': [make_model_code],
            'date': [date],
            'fuel': [fuel_code],
            'gear': [gear_code]
        })
        
        input_data = input_data[kolom_model]

        # Melakukan prediksi (Hasilnya dalam Euro)
        prediction_euro = model.predict(input_data)
        harga_tengah_euro = int(prediction_euro[0])

        # Konversi ke Rupiah
        KURS_EUR_TO_IDR = 17500
        harga_tengah_rupiah = harga_tengah_euro * KURS_EUR_TO_IDR

        # Membuat kisaran harga
        MARGIN_ERROR = 0.075 # Kisaran plus/minus 7.5%
        harga_minimum = harga_tengah_rupiah * (1 - MARGIN_ERROR)
        harga_maksimum = harga_tengah_rupiah * (1 + MARGIN_ERROR)

        with st.spinner('Model sedang menghitung...'):
            time.sleep(1)

        # Menampilkan hasil dalam bentuk kisaran harga
        formatted_harga_min = f"Rp {int(harga_minimum):,.0f}".replace(",", ".")
        formatted_harga_max = f"Rp {int(harga_maksimum):,.0f}".replace(",", ".")
        price_range_string = f"{formatted_harga_min} - {formatted_harga_max}"
        
        st.markdown(f"""
            <div style="background-color: rgba(0, 200, 0, 0.2); border-left: 8px solid #4CAF50; padding: 1rem; border-radius: 8px; margin-top: 1rem; text-align: center;">
                <p style="font-size: 1.2rem; color: white;">Kisaran Prediksi Harga Pasar:</p>
                <p style="font-size: 2.5rem; font-weight: bold; color: white;">{price_range_string}</p>
            </div>
            """, unsafe_allow_html=True)
        st.info(f"Catatan: Kisaran harga ini adalah estimasi ±{int(MARGIN_ERROR*100)}% dari harga prediksi model (€ {harga_tengah_euro:,}).")

    except FileNotFoundError:
        st.error("GAGAL MEMANGGIL MODEL. File 'motormodel.sav' atau 'model_mapping.csv' tidak ditemukan.")
    except Exception as e:
        st.error(f"TERJADI ERROR: {e}")

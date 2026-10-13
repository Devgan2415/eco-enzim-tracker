import streamlit as st
from datetime import datetime, timedelta
import sqlite3

# Konfigurasi halaman web
st.set_page_config(
    page_title="Pemantauan Eco-Enzyme",
    page_icon="🌿",
    layout="centered"
)

# --- INISIATOR DATABASE SQLITE ---
def init_db():
    conn = sqlite3.connect("eco_enzyme.db")
    cursor = conn.cursor()
    
    # 1. Buat tabel batches jika belum ada sama sekali
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS batches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            name TEXT NOT NULL,
            start_date TEXT NOT NULL,
            water REAL NOT NULL,
            organic REAL NOT NULL,
            sugar REAL NOT NULL,
            total_weight REAL NOT NULL
        )
    """)
    
    # 2. Cek apakah kolom 'username' sudah ada di tabel batches (untuk migrasi data lama)
    cursor.execute("PRAGMA table_info(batches)")
    columns = [info[1] for info in cursor.fetchall()]
    if "username" not in columns:
        cursor.execute("ALTER TABLE batches ADD COLUMN username TEXT NOT NULL DEFAULT 'DefaultUser'")

    # 3. Buat tabel journals jika belum ada
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS journals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            batch_id INTEGER,
            week_number INTEGER,
            log_date TEXT,
            symptom TEXT,
            diagnosis TEXT,
            solution TEXT,
            FOREIGN KEY (batch_id) REFERENCES batches (id)
        )
    """)
    conn.commit()
    conn.close()

init_db()

def get_connection():
    return sqlite3.connect("eco_enzyme.db")

# --- SISTEM LOGIN SEDERHANA ---
if "username" not in st.session_state:
    st.session_state["username"] = ""

st.sidebar.title("🔐 Akun Pengguna")
if not st.session_state["username"]:
    st.sidebar.info("Silakan masukkan nama/username Anda untuk mulai menggunakan aplikasi secara pribadi.")
    username_input = st.sidebar.text_input("Username / Nama Anda:")
    if st.sidebar.button("Masuk / Login", type="primary"):
        if username_input.strip():
            st.session_state["username"] = username_input.strip()
            st.rerun()
        else:
            st.sidebar.error("Username tidak boleh kosong!")
    st.stop() # Hentikan render halaman jika belum login
else:
    st.sidebar.success(f"Login sebagai: **{st.session_state['username']}**")
    if st.sidebar.button("Logout / Keluar"):
        st.session_state["username"] = ""
        st.rerun()

current_user = st.session_state["username"]

# --- JUDUL & NAVIGASI APLIKASI ---
st.title("🌿 Aplikasi Pemantauan Eco-Enzyme")
st.markdown(f"Halo, **{current_user}**! Kelola pembuatan, pantau jadwal fermentasi, dan catat jurnal kesehatan Eco-Enzyme Anda di sini.")

menu = st.sidebar.radio(
    "Navigasi Menu",
    [
        "1. Buat Batch & Hitung Rasio",
        "2. Dashboard & Jadwal Panen",
        "3. Jurnal Gejala & Diagnosis"
    ]
)

# --- MENU 1: BUAT BATCH ---
if menu == "1. Buat Batch & Hitung Rasio":
    st.header("🧪 Kalkulator & Buat Batch Baru")
    
    name = st.text_input("Nama/Kode Batch (Contoh: Jeruk_01)")
    calc_basis = st.radio(
        "Pilih dasar perhitungan:",
        ["Berdasarkan Volume Air (Liter)", "Berdasarkan Berat Bahan Organik (gram)"]
    )
    
    if "Air" in calc_basis:
        water_liter = st.number_input("Masukkan jumlah Air (Liter):", min_value=0.1, step=0.5, value=1.0)
        water = water_liter * 1000.0  # 1 Liter air = 1000 gram
        sugar = water / 10.0
        organic = sugar * 3.0
    else:
        organic = st.number_input("Masukkan jumlah Bahan Organik (gram):", min_value=0.0, step=50.0, value=300.0)
        sugar = organic / 3.0
        water = sugar * 10.0
        water_liter = water / 1000.0

    total_weight = water + organic + sugar
    start_date = datetime.today().strftime('%Y-%m-%d')

    st.markdown("---")
    st.subheader("📊 Hasil Komposisi (Rasio 1:3:10):")
    col1, col2 = st.columns(2)
    with col1:
        st.metric(label="Gula (1 bagian)", value=f"{sugar:.1f} g")
        st.metric(label="Bahan Organik (3 bagian)", value=f"{organic:.1f} g")
    with col2:
        st.metric(label="Air (10 bagian)", value=f"{water_liter:.1f} Liter ({water:.0f} g)")
        st.metric(label="Total Berat Campuran", value=f"{total_weight:.1f} g")
    
    st.write(f"📅 **Tanggal Mulai:** {start_date}")

    if st.button("💾 Simpan ke Database Saya", type="primary"):
        if not name.strip():
            st.error("Nama batch tidak boleh kosong!")
        else:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO batches (username, name, start_date, water, organic, sugar, total_weight)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (current_user, name, start_date, water, organic, sugar, total_weight))
            conn.commit()
            conn.close()
            st.success(f"Batch '{name}' berhasil disimpan untuk akun {current_user}!")

# --- MENU 2: DASHBOARD ---
elif menu == "2. Dashboard & Jadwal Panen":
    st.header("📊 Dashboard & Jadwal Panen")
    
    conn = get_connection()
    cursor = conn.cursor()
    # Hanya ambil batch milik user yang sedang login
    cursor.execute("SELECT id, name, start_date, water, organic, sugar FROM batches WHERE username = ?", (current_user,))
    batches = cursor.fetchall()
    
    if not batches:
        st.info("Belum ada batch terdaftar untuk akun Anda. Silakan buat batch baru di menu pertama.")
        conn.close()
    else:
        batch_dict = {f"ID: {b[0]} | Nama: {b[1]} (Mulai: {b[2]})": b[0] for b in batches}
        selected_label = st.selectbox("Pilih Batch yang ingin dipantau:", list(batch_dict.keys()))
        b_id = batch_dict[selected_label]

        cursor.execute("SELECT name, start_date, water, organic, sugar, total_weight FROM batches WHERE id = ?", (b_id,))
        selected = cursor.fetchone()
        conn.close()

        if selected:
            name, start_str, water, organic, sugar, total_weight = selected
            start_date = datetime.strptime(start_str, '%Y-%m-%d')
            today = datetime.today()
            days_elapsed = (today - start_date).days

            st.markdown(f"### Status Batch: `{name}`")
            st.metric(label="Usia Fermentasi", value=f"{days_elapsed} Hari")

            # Peringatan Fase Gas
            if days_elapsed <= 14:
                st.warning("🚨 **[Fase Pelepasan Gas]:** Buka tutup wadah sedikit setiap 1-2 hari sekali agar gas keluar dan wadah tidak meledak!")
            else:
                st.success("✅ Fase pelepasan gas intensif terlewati.")

            # Peringatan Batas Penambahan
            if 25 <= days_elapsed <= 35:
                st.info("⚠️ **[Batas Penambahan]:** Ini batas akhir penambahan bahan organik atau gula jika dirasa kurang.")

            # Jadwal Panen
            harvest_date = start_date + timedelta(days=90)
            days_to_harvest = (harvest_date - today).days
            
            st.markdown("---")
            if days_to_harvest > 0:
                st.info(f"⏳ **Perkiraan Panen:** {harvest_date.strftime('%Y-%m-%d')} (Kurang **{days_to_harvest} hari** lagi)")
            else:
                st.balloons()
                st.success("🎉 **Waktunya Panen!** Fermentasi sudah mencapai 3 bulan.")

# --- MENU 3: JURNAL GEJALA ---
elif menu == "3. Jurnal Gejala & Diagnosis":
    st.header("📝 Jurnal Gejala & Diagnosis")
    
    conn = get_connection()
    cursor = conn.cursor()
    # Hanya ambil batch milik user yang sedang login
    cursor.execute("SELECT id, name FROM batches WHERE username = ?", (current_user,))
    batches = cursor.fetchall()

    if not batches:
        st.info("Belum ada batch terdaftar untuk akun Anda.")
        conn.close()
    else:
        batch_dict = {f"ID: {b[0]} | Nama: {b[1]}": b[0] for b in batches}
        selected_label = st.selectbox("Pilih ID Batch:", list(batch_dict.keys()))
        b_id = batch_dict[selected_label]

        week_no = st.number_input("Minggu ke-:", min_value=1, max_value=20, value=1, step=1)

        choice = st.selectbox(
            "Pilih Gejala/Kondisi Permukaan:",
            [
                "1. Muncul lapisan putih / jamur putih",
                "2. Muncul jamur hitam, ulat, atau bau got/busuk",
                "3. Muncul lapisan seperti jeli (Mama Enzyme)"
            ]
        )

        diagnosis, solution = "", ""
        if "1." in choice:
            diagnosis = "Normal / Berhasil (Jamur pitera/ragi yang baik)."
            solution = "Biarkan saja atau aduk perlahan."
        elif "2." in choice:
            diagnosis = "Kontaminasi / Gagal Fermentasi."
            solution = "Tambahkan gula sejumlah takaran awal, tutup rapat, jemur di bawah matahari selama 3 hari."
        elif "3." in choice:
            diagnosis = "Sangat Berhasil (Struktur selulosa kaya manfaat)."
            solution = "Pertahankan penyimpanan, lapisan jeli (Mama Enzyme) bisa dipanen terpisah."

        st.markdown("---")
        st.markdown(f"**🔍 Diagnosis:** {diagnosis}")
        st.markdown(f"**💡 Solusi:** {solution}")

        if st.button("Simpan ke Jurnal"):
            cursor.execute("""
                INSERT INTO journals (batch_id, week_number, log_date, symptom, diagnosis, solution)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (b_id, week_no, datetime.today().strftime('%Y-%m-%d'), choice, diagnosis, solution))
            conn.commit()
            st.success("Jurnal berhasil disimpan!")

        # Tampilkan Riwayat Jurnal
        st.markdown("---")
        st.subheader("📖 Riwayat Jurnal Batch Ini")
        cursor.execute("SELECT week_number, log_date, symptom, diagnosis, solution FROM journals WHERE batch_id = ?", (b_id,))
        journals = cursor.fetchall()
        conn.close()

        if journals:
            for j in journals:
                with st.expander(f"Minggu ke-{j[0]} (Tanggal: {j[1]})"):
                    st.write(f"**Gejala:** {j[2]}")
                    st.write(f"**Diagnosis:** {j[3]}")
                    st.write(f"**Solusi:** {j[4]}")
        else:
            st.write("Belum ada catatan jurnal untuk batch ini.")

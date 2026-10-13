from datetime import datetime, timedelta
import sqlite3

# --- INISIATOR DATABASE SQLITE ---
def init_db():
    conn = sqlite3.connect("eco_enzyme.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS batches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            start_date TEXT NOT NULL,
            water REAL NOT NULL,
            organic REAL NOT NULL,
            sugar REAL NOT NULL,
            total_weight REAL NOT NULL
        )
    """)
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

def menu_buat_batch():
    print("\n--- 1. KALKULATOR & BUAT BATCH BARU ---")
    name = input("Nama/Kode Batch (Contoh: Jeruk_01): ")
    if not name.strip():
        print("Nama tidak boleh kosong!")
        return

    print("Pilih dasar perhitungan:")
    print("1. Berdasarkan Berat Air (gram/ml)")
    print("2. Berdasarkan Berat Bahan Organik (gram)")
    choice = input("Pilihan (1/2): ")

    if choice == '1':
        try:
            water = float(input("Masukkan jumlah Air (gram): "))
        except ValueError:
            print("Input harus angka!")
            return
        sugar = water / 10.0
        organic = sugar * 3.0
    else:
        try:
            organic = float(input("Masukkan jumlah Bahan Organik (gram): "))
        except ValueError:
            print("Input harus angka!")
            return
        sugar = organic / 3.0
        water = sugar * 10.0

    total_weight = water + organic + sugar
    start_date = datetime.today().strftime('%Y-%m-%d')

    print("\nHasil Komposisi (Rasio 1:3:10):")
    print(f"- Gula (1 bagian): {sugar:.1f} g")
    print(f"- Bahan Organik (3 bagian): {organic:.1f} g")
    print(f"- Air (10 bagian): {water:.1f} g")
    print(f"- Total Berat Wadah: {total_weight:.1f} g")
    print(f"- Tanggal Mulai: {start_date}")

    save = input("Simpan ke database? (y/n): ")
    if save.lower() == 'y':
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO batches (name, start_date, water, organic, sugar, total_weight)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (name, start_date, water, organic, sugar, total_weight))
        conn.commit()
        conn.close()
        print("Batch berhasil disimpan!")

def menu_dashboard():
    print("\n--- 2. DASHBOARD & JADWAL PANEN ---")
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, start_date, water, organic, sugar FROM batches")
    batches = cursor.fetchall()
    
    if not batches:
        print("Belum ada batch terdaftar.")
        conn.close()
        return

    print("Daftar Batch:")
    for b in batches:
        print(f"ID: {b[0]} | Nama: {b[1]} | Mulai: {b[2]}")

    try:
        b_id = int(input("Masukkan ID Batch yang ingin dipantau: "))
    except ValueError:
        print("ID harus angka!")
        conn.close()
        return

    cursor.execute("SELECT name, start_date, water, organic, sugar FROM batches WHERE id = ?", (b_id,))
    selected = cursor.fetchone()
    conn.close()

    if not selected:
        print("Batch tidak ditemukan.")
        return

    name, start_str, water, organic, sugar = selected
    start_date = datetime.strptime(start_str, '%Y-%m-%d')
    today = datetime.today()
    days_elapsed = (today - start_date).days

    print(f"\nStatus Batch: {name}")
    print(f"Usia Fermentasi: {days_elapsed} Hari")

    if days_elapsed <= 14:
        print("🚨 [Fase Pelepasan Gas]: Buka tutup wadah sedikit setiap 1-2 hari sekali agar tidak meledak!")
    else:
        print("✅ Fase pelepasan gas intensif terlewati.")

    if 25 <= days_elapsed <= 35:
        print("⚠️ [Batas Penambahan]: Ini batas akhir penambahan bahan/gula jika kurang.")

    harvest_date = start_date + timedelta(days=90)
    days_to_harvest = (harvest_date - today).days
    if days_to_harvest > 0:
        print(f"⏳ Perkiraan Panen: {harvest_date.strftime('%Y-%m-%d')} (Kurang {days_to_harvest} hari lagi)")
    else:
        print("🎉 Waktunya Panen! Sudah mencapai 3 bulan.")

def menu_jurnal():
    print("\n--- 3. JURNAL GEJALA & DIAGNOSIS ---")
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM batches")
    batches = cursor.fetchall()

    if not batches:
        print("Belum ada batch.")
        conn.close()
        return

    for b in batches:
        print(f"ID: {b[0]} | Nama: {b[1]}")

    try:
        b_id = int(input("Pilih ID Batch: "))
    except ValueError:
        print("ID harus angka.")
        conn.close()
        return

    try:
        week_no = int(input("Minggu ke-: "))
    except ValueError:
        print("Minggu harus angka.")
        conn.close()
        return

    print("\nPilih Gejala/Kondisi Permukaan:")
    print("1. Muncul lapisan putih / jamur putih")
    print("2. Muncul jamur hitam, ulat, atau bau got/busuk")
    print("3. Muncul lapisan seperti jeli (Mama Enzyme)")
    choice = input("Pilihan (1/2/3): ")

    diagnosis, solution = "", ""
    if choice == '1':
        diagnosis = "Normal / Berhasil (Jamur pitera/ragi yang baik)."
        solution = "Biarkan saja atau aduk perlahan."
    elif choice == '2':
        diagnosis = "Kontaminasi / Gagal Fermentasi."
        solution = "Tambahkan gula sejumlah takaran awal, tutup rapat, jemur di bawah matahari 3 hari."
    elif choice == '3':
        diagnosis = "Sangat Berhasil (Struktur selulosa kaya manfaat)."
        solution = "Pertahankan penyimpanan, lapisan jeli bisa dipanen terpisah."
    else:
        print("Pilihan tidak valid.")
        conn.close()
        return

    print(f"\nDiagnosis: {diagnosis}")
    print(f"Solusi: {solution}")

    save = input("Simpan ke jurnal? (y/n): ")
    if save.lower() == 'y':
        cursor.execute("""
            INSERT INTO journals (batch_id, week_number, log_date, symptom, diagnosis, solution)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (b_id, week_no, datetime.today().strftime('%Y-%m-%d'), f"Gejala Pilihan {choice}", diagnosis, solution))
        conn.commit()
        print("Jurnal berhasil disimpan!")
    conn.close()

def main():
    while True:
        print("\n=== APLIKASI PEMANTAUAN ECO-ENZYME ===")
        print("1. Buat Batch & Hitung Rasio")
        print("2. Dashboard & Jadwal Panen")
        print("3. Jurnal Gejala & Diagnosis")
        print("4. Keluar")
        
        opt = input("Pilih menu (1-4): ")
        if opt == '1':
            menu_buat_batch()
        elif opt == '2':
            menu_dashboard()
        elif opt == '3':
            menu_jurnal()
        elif opt == '4':
            print("Keluar dari program.")
            break
        else:
            print("Pilihan tidak valid.")

if __name__ == "__main__":
    main()

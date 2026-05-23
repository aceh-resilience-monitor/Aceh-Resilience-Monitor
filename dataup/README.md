# Data Pipeline API Bank Indonesia (PIHPS)

Folder `dataup` ini berisi sekumpulan skrip berbasis Node.js yang bertugas sebagai *pipeline* data mentah (*raw data*) untuk menarik data harga pangan komoditas secara dinamis dari API Bank Indonesia. 

Skrip dirancang dengan arsitektur idempotensi (bebas duplikasi), mekanisme *auto-retry* jaringan, dan dirancang khusus untuk diletakkan ke sistem *Task Scheduler* berbasis *Cloud* (contoh: Azure Functions Cron Job).

---

## 📂 Struktur File dan Fungsinya

### 1. `helper.js`
File ini adalah modul pendukung yang berisi sekumpulan fungsi inti (*core utilities*) yang akan dipanggil oleh skrip-skrip lainnya.
- **`fetchDataFromAPI(dateStr, regencyId, priceTypeId, retries)`**: Melakukan GET Request ke endpoint BI dengan implementasi *Auto-Retry* (maksimal 3 kali) apabila mendapatkan error `ECONNRESET` atau `ENOTFOUND` dari server.
- **`processApiData(...)`**: Mentransformasi struktur JSON bawaan API menjadi format data tabular *Flat Array* dengan membuang *dynamic keys* tanggal dan menambahkan kolom `komoditas`, `daerah`, serta `sumber`.
- **`logMessage(msg, isError)`**: Fungsi logger global yang mencetak output ke terminal sekaligus menyimpannya secara fisik ke `process.log` untuk kebutuhan audit.
- **Fungsi File System (`readJsonFile`, `writeJsonFile`, dll)**: Fungsi baca-tulis file JSON yang diletakkan di sub-folder `/data`.

### 2. `backfill.js`
Skrip *one-off* (dijalankan sesekali) yang berfungsi untuk merangkum seluruh data historis dari awal waktu (`2021-01-01`) hingga hari ini.
- Melakukan *looping* waktu per hari, dan menembak 12 kombinasi (3 daerah x 4 sumber).
- Menggunakan *delay* `500ms` per *request* agar tidak dianggap *spam* oleh *firewall* BI.
- Menyimpan hasil berdasar struktur tahunnya (contoh: `2021.json`, `2022.json`).

### 3. `daily_update.js`
Skrip otomatis yang dikhususkan untuk **Task Scheduler Harian**.
- Hanya memeriksa tanggal hari ini.
- Jika hari ini belum ada perilisan data (kosong), skrip otomatis mengecek mundur (*look back*) hingga **7 hari ke belakang** untuk menangkap rilis data yang terlambat.
- Menjalankan **Deduplikasi via Composite Key** (`tanggal|komoditas|daerah|sumber`) guna memastikan bahwa skrip harian ini tidak pernah memasukkan data yang sama dua kali. (Idempotent *safe*).

### 4. `retry_failed.js`
Skrip alat pemulihan (*Recovery Tool*) darurat jika proses penarikan data terputus di tengah jalan.
- Membaca file `process.log` secara otomatis dan mengekstrak pesan `[ERROR]`.
- Mendapatkan kombinasi tepat (Tanggal, Daerah, Sumber) yang sebelumnya gagal ditarik karena *timeout* atau pemutusan koneksi server.
- Melakukan pemanggilan ulang khusus untuk kombinasi yang gagal tersebut dan menggabungkannya ke dalam *database JSON* dengan aman.

---

## 🗄️ Format Data Hasil (Data Lake)

Seluruh output diletakkan di folder `dataup/data/YYYY.json`. 

Format penyimpanan sengaja didesain menggunakan **Flat Array / Tabular Form**. Praktik terbaik (*Best Practice*) Data Engineering untuk mempermudah injeksi lanjutan menuju Database SQL, pengolahan *Machine Learning* menggunakan _Pandas Python_, serta visualisasi dasbor _Business Intelligence_.

**Contoh Output:**
```json
[
  {
    "no": "I",
    "name": "Beras",
    "level": 1,
    "tanggal": "2021-01-04",
    "komoditas": "Beras",
    "harga": "10,500",
    "daerah": "Banda Aceh",
    "sumber": "Pasar Tradisional"
  }
]
```

---

## 🧪 Unit Testing

Pipeline ini dilengkapi dengan *test suite* komprehensif menggunakan **Jest** sebagai *test runner*. Testing dirancang untuk memenuhi kriteria **Modul 2: Software Engineering for Data Scientists** pada kurikulum AI Impact Challenge.

### Struktur File Test

```
dataup/
├── __tests__/
│   ├── helper.test.js          # 41 tests — Core utilities & API mocking
│   ├── daily_update.test.js    # 10 tests — Deduplication & idempotency
│   └── retry_failed.test.js    # 18 tests — Error log parsing & recovery
├── package.json                # Jest config, coverage thresholds, npm scripts
└── ...
```

### Cara Menjalankan Test

```bash
# Install dependencies (jika belum)
npm install

# Jalankan semua test dengan verbose output + coverage report
npm test

# Jalankan test dalam mode watch (auto-rerun saat file berubah)
npm run test:watch
```

### Coverage Report

| Metrik | Hasil | Target Minimum |
|:---|:---:|:---:|
| **Statements** | 95.71% | ≥ 80% ✅ |
| **Branches** | 92.30% | ≥ 70% ✅ |
| **Functions** | 100% | ≥ 80% ✅ |
| **Lines** | 95.45% | ≥ 80% ✅ |

### Apa yang Di-Test?

#### `helper.test.js` — Core Utilities (41 tests)
- **Konfigurasi Mapping**: Validasi `MAPPING_DAERAH` (3 kota Aceh) dan `MAPPING_SUMBER` (4 jenis pasar) untuk integritas data.
- **`processApiData()`**: Transformasi JSON API → Flat Tabular, termasuk *parent-child category assignment*, *dynamic date key extraction*, penanganan harga kosong (`-` dan `undefined` → `null`).
- **`readJsonFile()` & `writeJsonFile()`**: Baca-tulis JSON, penanganan file corrupt, file tidak ada, dan format indentasi.
- **`logMessage()`**: Logger dual-output (console + file), format timestamp, pemisahan `INFO` vs `ERROR`.
- **`fetchDataFromAPI()`**: *Mocked API calls* (tidak menembak server asli), validasi parameter request, mekanisme *auto-retry* hingga 3 kali, dan *graceful failure* setelah retry habis.
- **`delay()`**: Validasi async delay utility.

#### `daily_update.test.js` — Deduplikasi & Idempotensi (10 tests)
- **`generateKey()`**: Validasi format *composite key* (`tanggal|komoditas|daerah|sumber`).
- **Idempotensi**: Memastikan data identik menghasilkan key identik dan data berbeda menghasilkan key unik.
- **Simulasi Deduplikasi**: Memvalidasi bahwa `Map`-based deduplication mampu menolak duplikat dan menerima data baru secara bersamaan dalam satu batch.

#### `retry_failed.test.js` — Error Log Parsing & Recovery (18 tests)
- **Konsistensi Cross-Module**: Memastikan `generateKey()` di `retry_failed.js` menghasilkan format identik dengan `daily_update.js`.
- **Regex Parsing**: Validasi bahwa regex hanya menangkap baris `[ERROR]` dan mengabaikan `[INFO]`, `[WARN]`, dan `[SUCCESS]`.
- **Multi-line Parsing**: Simulasi parsing log lengkap, ekstraksi task gagal, deduplikasi error berulang, dan pengelompokan per tahun.

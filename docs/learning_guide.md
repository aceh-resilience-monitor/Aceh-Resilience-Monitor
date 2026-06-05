# 🎓 Panduan Pembelajaran: Meredesain, Mendeploy, & Menyelesaikan Error Proyek ARM

Dokumen ini dirancang khusus untuk membantu Anda memahami **konsep dan perintah (syntax) di balik pembangunan proyek ARM**, mulai dari inisialisasi awal, manajemen Git (termasuk menyelesaikan konflik), hingga konfigurasi cloud Azure. 

---

## 🧠 1. Skill & Pelajaran Utama dari Proyek Ini

Melalui proyek ARM ini, Anda telah mempelajari kombinasi skill tingkat industri (**Enterprise-Grade**) yang sangat dicari di dunia kerja saat ini:

1.  **MLOps (Machine Learning Operations):** Bukan hanya melatih model di notebook (seperti `.ipynb`), tetapi membawa model Prophet ke lingkungan produksi otomatis (Azure Functions) dan memantau kinerjanya setiap hari menggunakan **MLflow** dan **Azure ML Studio**.
2.  **Serverless & Cloud Architecture:** Memanfaatkan **Azure Functions** (Timer Trigger) untuk menjalankan komputasi terjadwal yang hemat biaya (skala dinamis dan arsitektur *pay-as-you-go*).
3.  **Cloud Security (Managed Identity):** Menghubungkan antar-layanan cloud secara aman tanpa menyimpan kata sandi/kredensial di kode program.
4.  **Data Engineering & ETL:** Membangun alur data dari Scraper (mengambil data web PIHPS), Pembersihan (menangani nilai kosong/`NaN`), hingga kompresi data untuk konsumsi dashboard.
5.  **Git Collaboration & CI/CD:** Menggunakan Git untuk branching, merging, dan memanfaatkan GitHub Actions untuk mendeploy dashboard otomatis ke **Azure Static Web Apps (SWA)**.

---

## 🛠️ 2. Perintah Pembangunan Awal (Dari Nol/Scratch)

Jika Anda ingin membuat proyek seperti ini dari awal di masa depan, berikut adalah urutan perintah pembangunannya:

### A. Inisialisasi Repositori Git Lokal
```bash
# 1. Membuat folder proyek baru dan masuk ke dalamnya
mkdir proyek-pangan && cd proyek-pangan

# 2. Menginisialisasi Git di komputer lokal Anda
git init

# 3. Membuat file README dan melakukan commit pertama
echo "# Proyek Pangan" > README.md
git add README.md
git commit -m "first commit"
```

### B. Membuat Proyek Azure Functions Lokal (Python)
Untuk membuat folder Azure Functions baru secara lokal:
```bash
# 1. Pastikan Anda memiliki Azure Functions Core Tools, lalu inisialisasi proyek Python
func init azure-functions --python -m V2

# 2. Pindah ke folder proyek Functions
cd azure-functions

# 3. Membuat fungsi baru dengan template Timer Trigger (penjadwalan)
func new --name arm_daily_pipeline --template "Timer trigger"
```
*   Perintah ini akan menghasilkan file `function_app.py` yang berisi template penjadwalan awal.

---

## 🌐 3. Perintah Konfigurasi Cloud Azure (Azure CLI)

Berikut adalah perintah CLI yang digunakan untuk merancang infrastruktur ARM di cloud:

### A. Membuat Resource Group (Wadah Utama)
```bash
az group create --name arm-datathon-rg --location southeastasia
```

### B. Membuat Storage Account (Tempat Menyimpan Data & Log)
```bash
az storage account create \
  --name armmlworkspace7422048783 \
  --resource-group arm-datathon-rg \
  --location southeastasia \
  --sku Standard_LRS
```

### C. Membuat Function App di Azure (Tempat Menjalankan Kode Python)
```bash
az functionapp create \
  --name arm-daily-pipeline-74220 \
  --resource-group arm-datathon-rg \
  --consumption-plan-location southeastasia \
  --runtime python \
  --runtime-version 3.11 \
  --functions-version 4 \
  --storage-account armmlworkspace7422048783 \
  --os-type Linux
```

---

## 🔀 4. Manajemen Git: Cabang (Branching) & Menyelesaikan Konflik

Dalam dunia industri, Anda **tidak boleh langsung mengedit cabang utama (`master`/`main`)**. Anda harus bekerja di cabang fitur Anda sendiri (misalnya, `aulia`).

### A. Alur Kerja Branching yang Benar
```bash
# 1. Membuat cabang baru bernama 'aulia' dan langsung pindah ke sana
git checkout -b aulia

# 2. Lakukan pengeditan kode Anda...

# 3. Simpan perubahan Anda secara berkala
git add .
git commit -m "feat: menambah modul analitik"
git push origin aulia
```

### B. Mengatasi Merge Conflict (Tabrakan Kode)
Conflict terjadi ketika rekan tim Anda dan Anda mengedit **baris yang sama di berkas yang sama**, lalu mencoba menggabungkannya (*merge*).

1.  **Ketika Anda melakukan `git merge aulia` di branch `master` dan terjadi conflict**, Git akan menghentikan proses merge dan menandai berkas yang tabrakan.
2.  Buka berkas yang bermasalah. Anda akan melihat penanda konflik bawaan Git seperti ini:
    ```python
    <<<<<<< HEAD
    # Kode yang ada di branch master saat ini
    url = "https://server-lama.com"
    =======
    # Kode baru yang Anda bawa dari branch aulia
    url = "https://server-baru-aktif.com"
    >>>>>>> aulia
    ```
3.  **Cara Menyelesaikan:**
    *   Diskusikan dengan tim kode mana yang benar.
    *   Hapus penanda konflik (`<<<<<<<`, `=======`, `>>>>>>>`) dan sisakan kode yang benar.
    *   Contoh hasil akhir setelah diedit manual:
        ```python
        url = "https://server-baru-aktif.com"
        ```
4.  **Selesaikan Proses Git setelah diedit:**
    ```bash
    # Tandai berkas yang konfliknya sudah selesai diperbaiki
    git add <nama_berkas_yang_conflict>

    # Selesaikan merge dengan commit
    git commit -m "merge branch aulia and resolve conflict"
    
    # Push ke GitHub
    git push origin master
    ```

---

## 🐞 5. Seni "Debugging" & Menyelesaikan Error (Troubleshooting)

Ketika program Anda error, jangan panik. Ikuti metode pemecahan masalah (debugging) tingkat industri ini:

### A. Membaca Traceback (Pesan Error Python)
*   **Lihat Baris Paling Bawah:** Pesan error utama selalu berada di baris paling bawah. Contoh: `FileNotFoundError: [Errno 2] No such file or directory` atau `TypeError: ...`.
*   **Lihat Call Stack:** Baca ke atas untuk melihat berkas dan baris ke berapa yang memicu error tersebut.

### B. Menangani Error Library Tidak Ditemukan (`ModuleNotFoundError`)
*   **Penyebab:** Modul Python yang di-import belum terinstal di server.
*   **Solusi Lokal:** Jalankan `pip install -r requirements.txt`.
*   **Solusi Cloud:** Tambahkan nama library tersebut (misalnya `mlflow==2.15.0`) ke dalam berkas `requirements.txt` di dalam folder `azure-functions`, lalu jalankan re-deploy (`func azure functionapp publish`).

### C. Menangani Error Koneksi Jaringan / Izin Akses
*   Jika server cloud Anda mencatat error akses ditolak (*Permission Denied* atau *Authentication Failed*):
    *   Periksa kembali konfigurasi hak akses Azure RBAC (peran *Contributor* / *Storage Blob Data Contributor*).
    *   Pastikan Connection String penyimpanan Azure Anda terisi dengan benar di bagian Application Settings.

---

## 🏆 6. Studi Kasus: 6 Masalah Nyata, Penyebab, & Solusinya

Berikut adalah daftar lengkap masalah nyata yang kita hadapi selama membangun proyek ini, apa penyebab teknisnya, dan bagaimana kita memecahkannya:

### 🔴 Masalah 1: Model Prophet yang Dilatih di Cloud Tidak Tercatat di Azure ML Studio
*   **Gejala:** Pipeline cloud berjalan sukses dan mencatat metrik harian ke `arm-daily-production`, namun 84 model Prophet yang dilatih secara dinamis di cloud tidak muncul di tab eksperimen Azure ML Studio.
*   **Penyebab Teknis:** Fungsi `setup_mlflow_tracking()` sebelumnya hanya dipanggil di bagian paling akhir program (Step 7). Akibatnya, pada Step 3 (saat melatih model Prophet), MLflow belum terhubung ke workspace Azure ML di cloud dan malah menyimpan log latihannya secara lokal di folder temporer kontainer Azure Function yang langsung hilang ketika kontainer mati.
*   **Solusi:** Memindahkan pemanggilan `setup_mlflow_tracking()` ke bagian awal eksekusi `arm_daily_pipeline` (tepat setelah inisialisasi logger). Ini memastikan MLflow global terhubung ke Azure ML Workspace sejak awal program berjalan.

### 🔴 Masalah 2: Error 404 pada Endpoint `/api/2.0/mlflow/logged-models` saat Logging Model
*   **Gejala:** Eksekusi pipeline terhenti di cloud dengan error 404 dari server REST API Azure ML Studio, atau TypeError pada `azureml_artifacts_builder()`.
*   **Penyebab Teknis:** Ketiadaan penguncian versi pada berkas requirements membuat `pip` otomatis memasang MLflow versi 3.x terbaru. Versi 3.x memanggil endpoint registrasi model baru yang belum didukung oleh server MLflow Azure ML Studio.
*   **Solusi:**
    1.  Mengunci versi MLflow secara ketat ke `mlflow==2.15.0` (versi stabil 2.x terakhir yang kompatibel) pada berkas `azure-functions/requirements.txt`.
    2.  Mengubah cara penyimpanan model: kita melewati fungsi bawaan `mlflow.prophet.log_model` yang bermasalah, lalu menyalin struktur model Prophet menjadi file JSON (`model_to_json`) dan mengunggahnya secara aman menggunakan fungsi dasar `mlflow.log_artifact(model_json_path, artifact_path="model")`.

### 🔴 Masalah 3: Masalah Keamanan Kredensial di Cloud (Ketiadaan berkas `config.json`)
*   **Gejala:** Kode program berjalan lancar di komputer lokal Anda karena ada berkas `config.json` lokal berisi kunci rahasia Azure, namun langsung error ketika dideploy ke cloud karena berkas tersebut diabaikan oleh `.gitignore` (untuk mencegah kebocoran kunci rahasia di GitHub).
*   **Penyebab Teknis:** Program di cloud tidak memiliki metode otentikasi aman untuk mengakses Azure ML Workspace.
*   **Solusi:** Menggunakan fitur bawaan Azure bernama **Managed Identity (MSI)**:
    1.  Mengaktifkan fitur Managed Identity pada resource Azure Function App.
    2.  Memberikan akses peran **Contributor** ke identitas Function App tersebut di tingkat Azure Resource Group.
    3.  Memperbarui fungsi `setup_mlflow_tracking` agar mendeteksi keberadaan variabel lingkungan cloud (`ARM_SUBSCRIPTION_ID`, dsb.) dan melakukan handshake menggunakan kelas `MsiAuthentication` bawaan SDK Azure ML.

### 🔴 Masalah 4: Browser Gagal Memuat Data Aktual (SyntaxError: Unexpected token 'N')
*   **Gejala:** Dashboard web gagal memuat data aktual terbaru dari cloud dan terpaksa menggunakan data fallback lokal. Konsol pengembang mencatat error parsing JSON.
*   **Penyebab Teknis:** Komoditas tertentu (seperti Cabai Rawit Merah) terkadang tidak memiliki data transaksi pada hari itu di web PIHPS, sehingga menghasilkan nilai kosong di Python berupa float `NaN`. Pustaka `json.dumps()` bawaan Python secara default mengekspor nilai `NaN` secara literal ke file JSON. Hal ini melanggar standar format JSON browser (yang hanya mengenal kata kunci `null`, bukan `NaN`).
*   **Solusi:** Membuat fungsi pembersihan rekursif `sanitize_nans` untuk memeriksa data secara menyeluruh dan mengganti semua nilai `NaN` menjadi `None` (yang otomatis diekspor sebagai nilai `null` standar JSON) sebelum berkas ditulis atau diunggah ke Blob.

### 🔴 Masalah 5: Error Pustaka Protokol Protobuf pada Terminal Lokal Anda (Python 3.14)
*   **Gejala:** Saat memverifikasi data lokal menggunakan perintah python, terminal mengeluarkan error panjang `TypeError: Metaclasses with custom tp_new are not supported`.
*   **Penyebab Teknis:** Perintah default `python3` di Mac Anda mengarah ke Python 3.14.3 (versi pratinjau eksperimental) di mana pustaka `protobuf` belum stabil dan mengalami konflik internal dengan kelas sistem.
*   **Solusi:** Memindai seluruh instalasi Python yang ada di Mac Anda, menemukan instalasi Python 3.13 milik Homebrew yang stabil, dan menjalankan perintah verifikasi secara spesifik menggunakan jalur `/opt/homebrew/bin/python3.13`.

### 🔴 Masalah 6: Run MLflow Menggantung (Running Selamanya) Setelah Re-Deploy
*   **Gejala:** Status eksekusi di Azure ML Studio terus-menerus bertanda "Running" dan data dashboard tidak terbarui meskipun program dilaporkan telah selesai.
*   **Penyebab Teknis:** Perintah pemicuan program (`curl`) dikirimkan tepat setelah proses deploy selesai. Azure Function sedang melakukan sinkronisasi pemicu (*syncing triggers*) dan daur ulang host (*host recycling*). Instance kontainer lama yang sedang memproses model Prophet dimatikan paksa oleh Azure sebelum program sempat menutup run MLflow (menyebabkan status menggantung).
*   **Solusi:** Menunggu beberapa menit agar status kontainer Azure Function stabil, lalu memicu ulang eksekusi bersih via `curl`.

---

## 💎 7. Empat Prinsip Rekayasa Perangkat Lunak Tingkat Lanjut

Selain pemecahan masalah teknis di atas, ada 4 prinsip desain sistem (*Software Engineering Best Practices*) sangat penting yang dapat Anda pelajari dari proyek ini:

### 1. Desain Resiliensi & Mekanisme Fallback (Graceful Degradation)
*   **Pelajaran:** Jangan biarkan kegagalan fitur tambahan mematikan sistem utama Anda.
*   **Contoh Kasus:** 
    *   Jika otentikasi Azure ML/MLflow gagal di cloud, program tidak berhenti (*crash*), melainkan melakukan **fallback otomatis** menggunakan SQLite lokal (`sqlite:///mlflow.db`).
    *   Jika penarikan data baru dari web scraper gagal (misalnya karena server web target mati), program akan menangkap exception (`try-except`) dan tetap melanjutkan eksekusi dengan memuat data historis terakhir yang ada di Blob Storage.

### 2. Validasi Dini Sebelum Deploy (Pre-flight Checks)
*   **Pelajaran:** Selalu lakukan pengujian sintaksis dan dependensi secara lokal sebelum mengunggah kode ke cloud untuk menghemat waktu dan mencegah kegagalan fatal.
*   **Contoh Kasus:** Sebelum menjalankan re-deploy Azure yang memakan waktu 8-10 menit, kita selalu menjalankan validasi sintaks python (`import ast; ast.parse(...)`) dan validasi *import* modul secara lokal. Ini mencegah siklus deploy berulang-ulang hanya karena kesalahan ketik (*typo*) sederhana.

### 3. Manajemen Sumber Daya Serverless (Resource & Timeout Tuning)
*   **Pelajaran:** Serverless cloud memiliki keterbatasan memori dan batas waktu eksekusi. Desain komputasi Anda harus efisien.
*   **Contoh Kasus:** Melatih 84 model Prophet dan mengunggah semua file bobotnya ke cloud sekaligus dapat menghabiskan kuota memori 1.5 GB dan melampaui batas waktu 10 menit Azure Function. 
*   Kita menyelesaikannya dengan cara **membatasi penyimpanan berkas bobot model (`model.json`) hanya untuk 21 model provinsi utama (aggregated)**, sedangkan 63 model tingkat wilayah kabupaten/kota lainnya cukup dicatat metrik performanya saja secara berkala.

### 4. Telemetri Terpusat (Centralized Telemetry)
*   **Pelajaran:** Pada infrastruktur serverless, Anda tidak memiliki akses langsung ke mesin fisik server. Oleh karena itu, pasang log monitoring yang terpusat sejak awal.
*   **Contoh Kasus:** Kita mengintegrasikan **Application Insights** ke dalam Azure Function App. Hal ini memungkinkan kita memantau setiap log kesalahan (`logger.info` / `logger.error`) dan melacak aktivitas sistem secara mendalam dari jarak jauh menggunakan perintah query Azure CLI tanpa perlu mengakses server secara langsung.

---

## 📈 8. Konsep Matematika & Logika Bisnis di Balik ARM

Memahami kode program saja tidak cukup; juri datathon biasanya sangat tertarik pada **metode ilmiah dan logika analitis** yang Anda gunakan. Berikut adalah konsep kunci di balik sistem intelijen pangan ARM:

### 1. Deteksi Anomali Reaktif: Z-Score dengan Moving Window
Sistem ARM mendeteksi anomali harga pangan hari ini menggunakan statistik Z-Score dinamis.
*   **Formula Z-Score:** 
    $$Z = \frac{Harga\_Hari\_Ini - \mu}{\sigma}$$
    *Di mana $\mu$ adalah rata-rata (mean) dan $\sigma$ adalah standar deviasi (std).*
*   **Logika Dinamis (Moving Window):** Kita tidak menggunakan rata-rata historis keseluruhan (global), melainkan menggunakan jendela bergerak **30 hari terakhir**.
*   **Mengapa?** Harga pangan bersifat musiman dan fluktuatif. Harga Cabai Rp 60.000 di bulan Desember (menjelang Tahun Baru) mungkin wajar, tetapi harga Rp 60.000 di bulan Maret bisa jadi merupakan anomali besar. Jendela bergerak memastikan sensitivitas model terhadap tren lokal jangka pendek.

### 2. Deteksi Dini Proaktif: Peramalan Prophet & Regressor Kebudayaan "Meugang"
Untuk memprediksi lonjakan harga 90 hari ke depan, ARM menggunakan pustaka peramalan time-series **Prophet** yang didekomposisi menjadi:
$$y(t) = g(t) + s(t) + h(t) + \epsilon_t$$
*Di mana $g(t)$ adalah tren, $s(t)$ adalah musiman harian/mingguan/tahunan, $h(t)$ adalah efek libur/hari besar, dan $\epsilon_t$ adalah error.*

*   **Poin Orisinalitas (Kearifan Lokal Aceh):** 
    Model time-series standar (seperti ARIMA atau Prophet dasar) tidak akan akurat memprediksi harga pangan di Aceh karena mereka tidak mengenal **Meugang** (tradisi memotong sapi/membeli daging di Aceh 1-2 hari menjelang Ramadan, Idul Fitri, dan Idul Adha).
*   **Logika Kode:** Kita menyuntikkan *custom holiday regressor* bernama `is_meugang_season` ke dalam model Prophet. Dengan mengajarkan model kapan terjadinya Meugang (berdasarkan kalender Hijriah yang dikonversi), model kita mampu memprediksi lonjakan harga daging dan cabai secara akurat sebelum peristiwa kebudayaan tersebut terjadi.

### 3. Analisis Arbitrase Harga Antar-Wilayah
Tab Spatial pada dashboard menghitung potensi keuntungan perdagangan (*price arbitrage*) untuk pedagang atau Satgas Pangan.
*   **Logika Bisnis:** Jika harga komoditas (misal Cabai Merah) di Kota Meulaboh jauh lebih murah dibandingkan di Kota Banda Aceh, sistem akan menghitung selisih harganya:
    $$\Delta P = Harga\_Banda\_Aceh - Harga\_Meulaboh$$
*   **Aturan Rekomendasi:** Jika $\Delta P$ melebihi estimasi biaya transportasi antar-kota, sistem akan memicu alert **Rekomendasi Arbitrase**. Ini membantu pemerintah melakukan intervensi pasar (subsidi transportasi atau operasi pasar terarah) untuk menyeimbangkan pasokan dan menekan inflasi daerah.

---

## 🏗️ 9. Arsitektur Infrastruktur Cloud & Alur Data (Data Flow)

Sebagai arsitek sistem, Anda harus bisa menjelaskan bagaimana data mengalir dari hulu ke hilir. Berikut adalah peta aliran data ARM:

```text
[ Web PIHPS ] (Sumber Data Pangan Nasional)
      │
      ▼ (Langkah 0: Scraper)
┌────────────────────────────────────────────────────────┐
│             Azure Function App (Compute)               │
│             «arm-daily-pipeline-74220»                │
├────────────────────────────────────────────────────────┤
│  1. Scraper berjalan di cloud, mengambil data hari ini │
│  2. Membaca data historis dari Storage Account         │
│  3. Melakukan Z-Score & Peramalan Prophet (84 model)   │
└───────────┬───────────────────────────────┬────────────┘
            │                               │
            │ (Langkah 6: Upload JSON)      │ (Langkah 7: Log MLflow via MSI)
            ▼                               ▼
┌──────────────────────────┐    ┌──────────────────────────┐
│      Azure Storage       │    │     Azure ML Studio      │
│  «armmlworkspace74220»   │    │    «arm-ml-workspace»    │
├──────────────────────────┤    ├──────────────────────────┤
│  Wadah "$web" (Public)   │    │  Eksperimen harian &     │
│  Menyimpan file:         │    │  registrasi parameter    │
│  dashboard_data.json     │    │  model secara terpusat   │
└───────────┬──────────────┘    └──────────────────────────┘
            │
            │ (Pemuatan Data via HTTPS GET / CORS)
            ▼
┌────────────────────────────────────────────────────────┐
│         Browser Pengguna / Client (Frontend)           │
│     «thankful-river-084494910.staticapps.net»          │
├────────────────────────────────────────────────────────┤
│  - Memuat file HTML/JS/CSS dari Static Web App (SWA)    │
│  - Mengambil data analitis langsung dari Blob Storage  │
│  - Merender visualisasi peta, chart, & EWS interaktif  │
└────────────────────────────────────────────────────────┘
```

### Penjelasan Aliran Data (Data Pipeline):
1.  **Ingestion (Scraping):** Azure Function bangun otomatis sesuai jadwal, lalu mengunduh data transaksi harga pangan hari ini dari situs PIHPS.
2.  **Storage (Raw Data):** Data tersebut langsung digabungkan dan disimpan ke dalam folder penyimpanan mentah di kontainer `arm-raw-data` (Storage Account).
3.  **Analytics Processing (Function App):** Kode analitik menghitung anomali Z-Score dan memicu 84 model Prophet.
4.  **Distribution (Public Blob Hosting):** Hasil analisis yang padat dan lengkap dikompresi menjadi satu file tunggal `dashboard_data.json`, lalu diunggah ke kontainer `$web` (yang bertindak sebagai repositori data publik).
5.  **Monitoring (MLflow & Telegram):** Secara paralel, Azure Function mengirimkan peringatan darurat ke **Telegram Satgas Pangan**, serta mencatatkan statistik latih model ke **Azure ML Studio** via MLflow.
6.  **Visualization (Static Web App):** Saat pengguna membuka dashboard web, browser mengunduh kerangka web dari SWA, lalu secara asinkron (AJAX/Fetch) mengunduh file `dashboard_data.json` dari Storage Blob untuk ditampilkan secara langsung.





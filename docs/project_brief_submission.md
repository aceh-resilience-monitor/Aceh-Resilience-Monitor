# 📋 Project Brief: Aceh Resilience Monitor (ARM)
**Datathon Dicoding × Microsoft Elevate Training Center 2026**

---

## 👥 1. Informasi Peserta

| No | Nama | Email Dicoding | Peran Utama & Atribusi Kode |
| :---: | :--- | :--- | :--- |
| 1 | **Aulia Muzhaffar** | auliamuzhaffar@gmail.com | *Machine Learning & Azure Specialist* (Logika *Forecasting* Prophet, Evaluasi Holdout, Azure ML & MLflow, Azure Functions Serverless Pipeline, Bug Fixing `NaN` ke `null`). |
| 2 | **Muhammad Ilhaam Ghiffari** | ilhaamghiffari@gmail.com | *Data Engineer & Frontend Developer* (Modular Refactoring ETL, Z-Score Anomaly Detection, Dasbor Dark Glassmorphism, Kompresi Payload JSON, CORS Configuration). |
| 3 | **Arief Hidayah** | ariefhidayahm@gmail.com | *QA Auditor, Repo Manager & Storyteller* (Scraping Data PIHPS, Unit Testing Pytest, Laporan Arsitektur Cloud & Error Analysis, Q&A Drill, Alert Telegram Bot). |

*   **Topik Proyek:** Ketahanan Pangan & Agrikultur Modern
*   **Status Produk:** 🚀 **100% Selesai & Terverifikasi Cloud**
*   **Tautan Dasbor Live:** [https://thankful-river-084494910.7.azurestaticapps.net](https://thankful-river-084494910.7.azurestaticapps.net)
*   **Tautan Repositori GitHub:** [https://github.com/aceh-resilience-monitor/Aceh-Resilience-Monitor.git](https://github.com/aceh-resilience-monitor/Aceh-Resilience-Monitor.git)

---

## 🎯 2. Ringkasan Eksekutif

### Latar Belakang Masalah
Volatilitas harga pangan strategis (*volatile foods*) merupakan salah satu penyumbang inflasi daerah terbesar di Indonesia. Di Provinsi Aceh, tantangan ini diperparah oleh:
1.  **Lambatnya Integrasi Data:** Proses pengumpulan data harga di pasar-pasar tradisional masih dilakukan secara manual atau terpisah antara portal seperti PIHPS dan SP2KP, memicu jeda analisis hingga beberapa hari.
2.  **Respons yang Bersifat Reaktif:** Instansi pemerintah (TPID/Satgas Pangan) umumnya baru melakukan intervensi (seperti Operasi Pasar Murah) setelah harga pangan melambung tinggi di pasar konsumen (*hilir*).
3.  **Ketiadaan Prediksi Tren:** Pemangku kebijakan tidak memiliki instrumen cerdas untuk memproyeksikan pergerakan harga komoditas pangan esensial ke depan berdasarkan siklus hari raya lokal.

### Problem Statement
Bagaimana membangun sistem otomatisasi terintegrasi yang mampu mengumpulkan data harga pangan harian secara serverless, mendeteksi anomali harga harian, dan meramal lonjakan harga 90 hari ke depan guna menyajikan rekomendasi kebijakan stabilisasi pasar secara preventif?

### Research Questions
1.  Komoditas apa saja yang saat ini menunjukkan anomali harga kritis di luar batas deviasi wajar ($2\sigma$) terhadap rata-rata bulanan (MA30)?
2.  Komoditas apa saja yang diprediksi oleh Machine Learning akan mengalami lonjakan harga ekstrem ($\ge 20\%$) dalam 90 hari ke depan?

### Mengapa Memilih Proyek Ini (Painkiller Concept)
Aceh Resilience Monitor (ARM) bertindak sebagai *painkiller* nyata (bukan sekadar *vitamin* visualisasi data biasa) yang langsung menyelesaikan rasa sakit birokrasi dalam merespons inflasi. Melalui integrasi otomatisasi cloud serverless Azure (biaya $0/bulan), dasbor analisis margin rantai pasok, dan pengiriman alert otomatis ke bot Telegram, ARM mendeteksi ancaman lonjakan harga pangan sebelum terjadi sehingga pemerintah dapat melaksanakan Operasi Pasar secara preventif untuk melindungi daya beli masyarakat miskin di Provinsi Aceh.

---

## 📄 3. Deskripsi Project

### Nama Produk, Fungsi, & Cara Penyelesaian Masalah
*   **Nama Produk:** Aceh Resilience Monitor (ARM) — Dashboard Intelijen Harga Pangan.
*   **Fungsi:** Platform analitik berbasis web interaktif untuk mendeteksi anomali harga pangan historis secara harian dan memproyeksikan pergerakan harga 21 komoditas pangan esensial di Aceh hingga 90 hari ke depan.
*   **Penyelesaian Masalah:** ARM memotong rantai respons birokrasi yang lambat dengan menyajikan *Early Warning System* visual yang mendeteksi ancaman kenaikan harga *sebelum* berdampak ke pasar hilir konsumen, lengkap dengan bot peringatan Telegram harian dan rekomendasi taktis preventif (seperti pemicuan operasi pasar).

### Target Pengguna & Value Proposition
*   **Target Pengguna:**
    *   *Tim Pengendalian Inflasi Daerah (TPID) Provinsi Aceh:* Pengambil kebijakan stabilisasi harga daerah.
    *   *Satgas Pangan Provinsi Aceh:* Tim pemeriksa rantai pasok dan pelaksana operasi pasar di lapangan.
    *   *Dinas Perindustrian & Perdagangan (Disperindag):* Pengelola kuota cadangan pangan daerah.
*   **Value Proposition:**
    *   *Explainable & Actionable AI:* Sistem tidak hanya memprediksi, tetapi juga menerangkan "mengapa" harga naik (musiman/rantai pasok) dan merekomendasikan "aksi apa" yang harus diambil (seperti Operasi Pasar Murah Cabai Merah).
    *   *Zero Cost Infrastructure:* Seluruh ekosistem berjalan di Azure Free Tier dengan biaya operasional $0/bulan.
    *   *High Performance Web:* Kecepatan loading dasbor sangat cepat (<1.5 detik) berkat kompresi data hulu.

### Arsitektur Sistem & Data Pipeline
Aliran data ARM dirancang secara serverless untuk menghindari kerumitan pemeliharaan server fisik (*zero-maintenance infrastructure*):

```mermaid
flowchart TB
    subgraph INGESTION ["📥 Ingestion & In-Memory ETL"]
        A1["🌐 PIHPS Web Scraper"] -->|daily update| B1["Azure Blob Storage<br/>(arm-raw-data)"]
        B1 -->|combine in memory| C1["scripts/etl.py<br/>load_all_data() + add_holiday_features()"]
    end

    subgraph ANALYTICS ["🧠 In-Memory Processing & MLOps"]
        C1 --> D1["scripts/anomaly.py<br/>Z-Score + MA30"]
        C1 --> D2["scripts/forecast.py<br/>84 Prophet Models (RAM)"]
        D2 -->|Log metrics harian| E1["Azure ML Studio<br/>(MLflow API)"]
    end

    subgraph OUTPUT ["📤 serve layer"]
        D1 & D2 --> F1["prepare_dashboard_data.py<br/>(Resampling & JSON Compression)"]
        F1 -->|upload dashboard_data.json| G1["Azure Blob Storage<br/>($web container)"]
        F1 -->|If anomaly / EWS spike| H1["Telegram Bot API<br/>(Satgas Pangan Alerts)"]
    end

    subgraph CONSUMER ["🌐 End-User Interaction"]
        G1 --> I1["Azure Static Web Apps<br/>(CORS configured)"]
        I1 --> J1["📊 Web Dashboard<br/>(Client-side Chart.js)"]
    end
```

---

## 🛠️ 4. Fitur Utama dan Teknologi yang Digunakan

### Fitur Utama Produk
*   **Predictive Early Warning System (EWS) Cards:** Tampilan visual interaktif berupa kartu yang menyoroti 3 komoditas paling rentan mengalami lonjakan harga ekstrem dalam 90 hari ke depan.
*   **Actionable Insight AI (Meta Prophet):** Setiap kartu EWS secara otomatis menyertakan label bahaya (seperti EKSTREM atau WASPADA) beserta rekomendasi tindakan strategis konkret bagi pemerintah daerah.
*   **Historical Process Control Anomaly Detection:** Pendeteksian lonjakan harga tak wajar (*spikes*) berdasarkan perhitungan statistik Z-Score (simpangan baku) dan rata-rata bergerak 30 hari (MA30).
*   **Interactive Forecast Charts & YoY Analysis:** Visualisasi data interaktif per komoditas yang dilengkapi sakelar (*toggle*) untuk memunculkan garis tren masa lalu dan garis batas atas/bawah prediksi harga di masa depan.
*   **Data Compression Engine:** Pengompresi ukuran data dasbor harian hingga 85% (~509 KB) melalui *weekly resampling* untuk menjamin kecepatan muat dasbor di bawah 1.5 detik.

### Teknologi Perangkat Lunak & Infrastruktur Cloud
*   **Bahasa Utama:** Python 3.11 (backend & cloud pipeline), JavaScript (Chart.js & Leaflet.js frontend).
*   **Libraries:** Pandas, NumPy, Meta Prophet, Pytest, Requests, MLflow, AzureML SDK.
*   **Desain Antarmuka:** HTML5, Vanilla CSS (Glassmorphism, custom grid).
*   **Azure Blob Storage:** Digunakan sebagai *Data Lake* harian untuk menyimpan data harga mentah tahunan (`2021.json` s/d `2026.json`) secara terstruktur di container privat `arm-raw-data`. Layanan ini juga digunakan sebagai hosting data serving dasbor publik (`dashboard_data.json`) pada container `$web` yang telah dikonfigurasi dengan aturan CORS terpusat.
*   **Azure Functions:** Bertindak sebagai *serverless orchestrator* harian. Berjalan otomatis pada pukul 08:00 WIB (Timer Trigger) menggunakan runtime Python 3.11 dengan konfigurasi timeout 10 menit. Tugasnya adalah mengeksekusi scraper, prapemrosesan data, kalkulasi Z-Score, training model Prophet secara in-memory, pengiriman alert Telegram, dan pembaharuan berkas JSON.
*   **Azure Machine Learning Studio (MLflow):** Digunakan sebagai platform MLOps terintegrasi untuk memantau performa model. Melacak dan mencatat metrik evaluasi (MAPE, MAE, RMSE) dari 84 model Prophet harian untuk mendeteksi *data/concept drift* serta mempermudah reproduksibilitas model.
*   **Azure Static Web Apps:** Hosting dasbor frontend (HTML/CSS/JS) serverless yang terintegrasi secara otomatis dengan repositori GitHub dengan SSL otomatis.

### Machine Learning & Forecasting Components
Pemodelan time-series menggunakan algoritma **Meta Prophet** dengan penambahan parameter *Extra Regressors* untuk menangani hari raya keagamaan dan musim lokal di Aceh:
*   **Fitur Kearifan Lokal (Local Wisdom Regressors):**
    *   `is_meugang_season`: Mengidentifikasi tradisi H-2 s/d H-0 menyembelih sapi menjelang Ramadan & Lebaran (mengantisipasi *demand shock* daging sapi & bumbu).
    *   `is_ramadan_prep`: Persiapan pangan H-7 s/d H-1 awal puasa.
    *   `is_nataru`: Liburan Natal & Tahun Baru (20 Des – 2 Jan).
    *   `is_wet_season`: Musim hujan Aceh (Oktober – April) dari data BMKG untuk mengantisipasi *supply shock* cabai dan bawang.
*   **Metode Validasi:** *Time-based Holdout Split (90 Hari)* untuk memastikan model diuji pada data yang belum pernah dilihat.
*   **Metrik Evaluasi:**
    *   Rata-rata MAPE komoditas stabil (Daging Sapi & Beras): **0.49% – 2.2%** (Akurasi Sangat Tinggi).
    *   Rata-rata MAPE komoditas volatil (Cabai & Bawang): **20% – 32%** (Akurasi Cukup, dipengaruhi faktor eksternal cuaca).
    *   Rata-rata MAPE Agregat (21 Komoditas): **7.74%** (Mengurangi error baseline hingga 22%).

### Dashboard & Visualisasi (Antarmuka Pengguna)
Dasbor dirancang dengan gaya **Dark Glassmorphism** modern yang responsif dan terbagi atas 4 tab fungsional utama:
1.  **Tab Dashboard Utama (Executive Home):** Menampilkan KPI utama harga rata-rata provinsi, persentase inflasi tahunan berjalan, tingkat volatilitas (CV), serta Early Warning System (EWS) panel yang menyoroti 3 komoditas paling terancam lonjakan harga dalam 3 bangsa ke depan.
2.  **Tab Analisis Spasial (Peta Interaktif):** Peta GIS berbasis Leaflet.js yang mewarnai kota Banda Aceh, Lhokseumawe, dan Meulaboh berdasarkan tingkat keparahan anomali harian (🟢 Hijau = Normal, 🟡 Kuning = Waspada, 🔴 Merah = Kritis).
3.  **Tab Kesehatan Rantai Pasok (Margin Rantai Pasok):** Memvisualisasikan selisih margin harga secara vertikal dari tingkat Produsen $\rightarrow$ Pedagang Besar $\rightarrow$ Pasar Tradisional $\rightarrow$ Pasar Modern untuk mendeteksi potensi aksi penimbunan (*hoarding*).
4.  **Tab Tren Mingguan & Prediksi:** Menampilkan grafik interaktif Chart.js lengkap dengan bayangan area keyakinan (*confidence interval* prediksi atas/bawah) 90 hari ke depan.

### Status Implementasi Proyek Saat Ini
Proyek ARM saat ini berstatus **100% Selesai & Teruji** untuk seluruh fungsionalitas inti.
*   **Modul Ingestion & ETL:** 100% Selesai. Pengumpulan otomatis data PIHPS berjalan lancar tanpa duplikasi.
*   **Modul Analytics & Machine Learning:** 100% Selesai. 84 model Prophet dilatih secara paralel di RAM Functions dan metrik dievaluasi di Azure ML Studio.
*   **Modul Early Warning & Telegram Bot:** 100% Selesai. Telegram Bot aktif mengirimkan alert berkala lengkap dengan rekomendasi intervensi.
*   **Modul Dasbor & Visualisasi:** 100% Selesai. Terintegrasi dengan storage CORS dan data terkompresi bebas error `NaN`.
*   **Modul Pengujian & Kualitas Kode:** 100% Selesai. Memiliki 56 unit tests otomatis (**56 passed**).
*   **Dokumentasi Pengembang:** 100% Selesai. Berkas [`run_guide.md`](file:///Users/auliamuzhaffar/Documents/Datathon/datathon-dicoding/run_guide.md) dan [`docs/learning_guide.md`](file:///Users/auliamuzhaffar/Documents/Datathon/datathon-dicoding/docs/learning_guide.md) telah tersedia secara lokal.

---

## 📄 5. Cara Penggunaan Product

Berikut adalah alur penggunaan platform **Aceh Resilience Monitor (ARM)** dari sudut pandang pengguna akhir (Tim Pengendalian Inflasi Daerah / TPID, Satgas Pangan Provinsi Aceh, serta Pengambil Kebijakan Daerah):

### 🌐 Akses Platform
*   **Tautan Live Dashboard:** [https://thankful-river-084494910.7.azurestaticapps.net](https://thankful-river-084494910.7.azurestaticapps.net)
*   **Akses Login (Kredensial Demo):** Platform dasbor dirancang sebagai instrumen transparansi ketahanan pangan dan pendukung keputusan publik dengan sifat **bebas hambatan (zero friction)**. Oleh karena itu, platform **tidak memerlukan login/kredensial khusus (Akses Terbuka/Publicly Accessible)** agar juri maupun pejabat daerah dapat langsung melakukan pemantauan harga pangan strategis tanpa kendala otentikasi.

---

### 🚶‍♂️ Alur & Langkah Penggunaan Dasbor (Step-by-Step)

#### 1. Pemantauan Makro (Tab "Executive")
*Tujuan: Mendapatkan gambaran umum stabilitas pangan daerah dalam 3 detik.*
*   **Langkah 1:** Buka tautan dasbor. Pengguna akan langsung diarahkan ke halaman utama **Executive**.
*   **Langkah 2:** Periksa kartu metrik utama di bagian atas untuk melihat rata-rata harga provinsi, inflasi tahunan, dan indeks volatilitas.
*   **Langkah 3:** Tinjau **Peta Anomali Harga Spasial** di tengah halaman. Cari wilayah kabupaten/kota yang menyala dengan warna **Merah (Kritis, Z-Score > 3σ)** atau **Kuning (Waspada, Z-Score > 2σ)**.
*   **Langkah 4:** Tinjau bagian **Sistem Peringatan Dini (EWS)** untuk membaca daftar log anomali harga komoditas pangan esensial yang melonjak melampaui batas deviasi wajar hari ini.

![Executive Tab Dashboard](file:///Users/auliamuzhaffar/Documents/Datathon/datathon-dicoding/docs/images/executive_tab_live.png)

#### 2. Analisis Spasial & Peluang Arbitrase (Tab "Spatial")
*Tujuan: Mendeteksi disparitas harga antar wilayah utama dan merumuskan operasi pasar.*
*   **Langkah 1:** Klik tab **Spatial** pada bar navigasi.
*   **Langkah 2:** Pilih komoditas spesifik pada dropdown selektor komoditas (misalnya: *Cabai Merah* atau *Bawang Merah*).
*   **Langkah 3:** Sistem akan membandingkan tren harga secara historis di 3 daerah pantauan utama: **Banda Aceh**, **Lhokseumawe**, dan **Meulaboh**.
*   **Langkah 4:** Baca kartu rekomendasi **Arbitrage Advisor** di bagian bawah. Jika ada komoditas dengan disparitas harga ekstrem (>30%) antar wilayah, sistem akan menyarankan rekomendasi logistik (misalnya: memindahkan pasokan dari produsen surplus Lhokseumawe untuk meredam harga di Banda Aceh).

![Spatial Tab Dashboard](file:///Users/auliamuzhaffar/Documents/Datathon/datathon-dicoding/docs/images/spatial_tab_live.png)

#### 3. Audit Rantai Pasokan & Deteksi Spekulan (Tab "Margin")
*Tujuan: Mendeteksi indikasi penimbunan bahan pokok (hoarding) oleh oknum kartel.*
*   **Langkah 1:** Klik tab **Margin** pada bar navigasi.
*   **Langkah 2:** Sistem menampilkan representasi visual diagram alur rantai distribusi pangan dari tingkat **Produsen** $\rightarrow$ **Pedagang Besar** $\rightarrow$ **Pasar Tradisional** $\rightarrow$ **Pasar Modern**.
*   **Langkah 3:** Cari komoditas yang memiliki label status **Kritis (Merah)** dengan markup margin kotor melebihi **40%**.
*   **Langkah 4:** Tim Satgas Pangan dapat menggunakan data disparitas vertikal ini sebagai dasar hukum untuk melakukan inspeksi mendadak (sidak) ke gudang pedagang besar yang mencurigakan.

![Margin Tab Dashboard](file:///Users/auliamuzhaffar/Documents/Datathon/datathon-dicoding/docs/images/margin_tab_live.png)

#### 4. Proyeksi Inflasi 90 Hari ke Depan (Tab "ML EWS")
*Tujuan: Perencanaan preventif operasi pasar murah sebelum lonjakan harga terjadi.*
*   **Langkah 1:** Klik tab **ML EWS** pada bar navigasi.
*   **Langkah 2:** Tinjau panel **Early Warning System (Meta Prophet AI)** yang menyoroti 3 komoditas dengan risiko kenaikan harga tertinggi dalam 90 hari mendatang.
*   **Langkah 3:** Pilih kategori komoditas pada bagian grafik tren untuk memicu visualisasi peramalan waktu.
*   **Langkah 4:** Klik tombol **"Tampilkan Prediksi 90 Hari"** pada grafik Chart.js.
*   **Langkah 5:** Amati visualisasi bayangan area keyakinan prediksi (*confidence interval* batas atas & batas bawah). Jika proyeksi menembus batas kritis inflasi bertepatan dengan momen hari raya (misalnya H-2 Meugang), TPID dapat segera menjadwalkan Operasi Pasar Murah sebulan sebelum tanggal proyeksi puncak lonjakan harga.

![ML EWS Tab Dashboard](file:///Users/auliamuzhaffar/Documents/Datathon/datathon-dicoding/docs/images/ml_ews_tab_live.png)

---

### 🔔 Notifikasi Alert Telegram (Saluran Komunikasi Cepat)
*   Selain melalui dasbor, seluruh jajaran Satgas Pangan dan TPID Aceh yang tergabung dalam grup koordinasi akan menerima pesan teks otomatis dari **ARM Telegram EWS Bot** setiap pagi pukul 08:00 WIB.
*   **Isi Pesan:** Informasi deteksi anomali real-time pagi hari, komoditas dengan proyeksi kenaikan kritis 90 hari mendatang, serta lampiran rekomendasi aksi konkret (Operasi Pasar/Intervensi Logistik).

---

## 📂 6. Informasi Pendukung

### 🥩 1. Studi Kasus Pengguna (User Case Study)
*   **Kasus:** Pemantauan Harga Daging Sapi Kualitas 1 di Banda Aceh Menjelang Tradisi Meugang (Juni 2026).
*   **Permasalahan:** Menjelang hari besar keagamaan, terjadi lonjakan harga daging sapi yang sangat tinggi di pasar-pasar tradisional Kota Banda Aceh. TPID Kota Banda Aceh perlu mengidentifikasi apakah lonjakan harga ini wajar akibat peningkatan permintaan (*demand shock*) atau disebabkan oleh penimbunan stok (*supply hoarding*) di tingkat pedagang eceran.
*   **Langkah Analisis Menggunakan ARM:**
    1.  **Identifikasi Anomali (Tab Executive):** Z-Score harian pada dashboard mendeteksi deviasi harga daging sapi menyimpang hingga **+16.1%** dari rata-rata bulanan (MA30). Status komoditas berubah menjadi *Waspada*.
    2.  **Audit Rantai Pasok (Tab Margin):** Peneliti TPID mengecek diagram alur rantai distribusi. Ditemukan harga di tingkat Pedagang Besar (Grosir/Distributor) adalah `Rp 165.000` sedangkan di Pasar Tradisional (Eceran) adalah `Rp 170.000`.
    3.  **Kalkulasi Margin:**
        $$\text{Margin Keuntungan Eceran} = \frac{170.000 - 165.000}{165.000} \times 100\% = \mathbf{3.03\%}$$
    4.  **Rekomendasi Kebijakan:** Karena margin pedagang eceran sangat tipis (hanya 3.03% atau selisih Rp 5.000/kg), TPID menyimpulkan **rantai pasok retail sangat sehat dan efisien**; kenaikan harga murni didorong oleh guncangan permintaan musiman (Meugang) di tingkat grosir/hulu, bukan spekulan retail.
    5.  **Aksi Nyata:** Satgas Pangan tidak perlu melakukan razia/sidak di tingkat pasar tradisional, melainkan berfokus mendistribusikan subsidi logistik pengangkutan hewan ternak dari peternak surplus di Lhokseumawe ke distributor Banda Aceh guna meredam harga grosir.

---

### 🔮 2. Rencana Pengembangan ke Depan (Future Roadmap)

Untuk menjamin keberlanjutan, akurasi peramalan, dan skalabilitas sistem Aceh Resilience Monitor (ARM), kami merancang peta jalan pengembangan lanjutan yang terbagi menjadi 4 Fase Taktis serta 3 Pilar Rekayasa Utama:

#### 📋 Ringkasan Fase Strategis
*   **FASE 1: Pilot Project TPID (Q3 2026)**
    → Uji coba operasional dasbor di lingkungan Satgas Pangan & TPID Provinsi Aceh untuk menyelaraskan alur kerja taktis.
*   **FASE 2: Analisis Korelasi Lintas Pangan (Q4 2026)**
    → Pendeteksian rambatan inflasi antarkomoditas (misal: kenaikan harga pakan jagung ➔ efek domino 7 hari kemudian pada komoditas telur dan daging ayam).
*   **FASE 3: Machine Learning Multivariat (Q1 2027)**
    → Integrasi data cuaca curah hujan dari BMKG API, data produksi lokal, serta fluktuasi biaya BBM transportasi ke model ML multivariat (seperti Prophet Multivariat atau XGBoost).
*   **FASE 4: Rekayasa Kualitas Data & Optimasi Skalabilitas Pipeline (Peta Jalan Teknis)**
    → Implementasi infrastruktur penanganan data cerdas, penjagaan kualitas data latih model, dan optimalisasi paralelisasi komputasi awan.

---

#### 🗂️ Detail Pengembangan Teknis (Fase 4)

##### 1. Pilar 1: Rekayasa Kualitas & Integrasi Data (Data Engineering)
Fokus utama pilar ini adalah untuk memastikan ketersediaan data harian selalu bersih, bebas dari kesalahan rilis, dan tahan terhadap gangguan server pihak ketiga.
*   **Penanganan Batas Pergantian Tahun (*Year-End Boundary Lookback*)**
    *   *Deskripsi*: Modifikasi scraper agar mendeteksi tahun dari setiap data tanggal yang berhasil di-scrape secara dinamis.
    *   *Tujuan*: Menjamin data *lookback* di akhir tahun (misalnya tanggal 30-31 Desember) yang di-scrape pada awal Januari tetap masuk ke berkas tahun yang benar (misalnya `2026.json` bukan `2027.json`).
*   **Deteksi Gap Otomatis (*Self-Healing Backfill*)**
    *   *Deskripsi*: Membuat subsistem pemindai data harian yang mendeteksi hari-hari kosong dalam 30 hari terakhir. Jika ditemukan hari kosong (akibat server BI mati lama), sistem otomatis membuat antrean penarikan data (*backfill queue*) saat server BI kembali *online*.
    *   *Tujuan*: Menutup celah data (*data gaps*) secara otomatis tanpa intervensi manual dari administrator.
*   **Penyelarasan Nama Komoditas Dinamis (*Fuzzy String Matching*)**
    *   *Deskripsi*: Menggunakan algoritma jarak Levenshtein (`difflib` di Python) untuk memetakan nama komoditas dari API BI ke standar ARM secara adaptif.
    *   *Tujuan*: Mencegah kegagalan ETL ketika admin BI Hargapangan mengubah nama komoditas secara tiba-tiba (seperti penambahan spasi atau tanda kurung satuan).

##### 2. Pilar 2: Optimasi Model & Machine Learning (MLOps & Analytics)
Fokus utama pilar ini adalah menjaga stabilitas performa model peramalan Meta Prophet dari gangguan *noise* data ekstrem.
*   **Pelatihan Jendela Bergerak (*Sliding Window Training - 730 Days*)**
    *   *Deskripsi*: Membatasi sejarah data latih Prophet secara konstan hanya untuk data **2 tahun terakhir (730 hari)**.
    *   *Tujuan*: Menghindari *Concept Drift* (data lama tahun 2021-2022 sudah tidak relevan dengan perilaku pasar tahun 2026) dan memotong waktu eksekusi pelatihan.
*   **Penyaringan Outlier Ekstrem (*Data Winsorization / Clipping*)**
    *   *Deskripsi*: Menerapkan pemotongan harga otomatis pada data latih jika terdeteksi lonjakan anomali sesaat ($> 3\sigma$).
    *   *Tujuan*: Menjaga agar garis tren peramalan Prophet tidak rusak akibat fluktuasi jangka pendek yang ekstrem.
*   **Imputasi Data Kosong ML (*Forward Fill Constraint*)**
    *   *Deskripsi*: Mengisi kekosongan data jangka pendek (akhir pekan/hari libur) secara dinamis menggunakan harga terakhir yang dilaporkan (maksimum 7 hari berturut-turut) sebelum dimasukkan ke model pelatihan.
    *   *Tujuan*: Menjaga deret waktu tetap kontinu agar model Prophet tidak bias atau mengalami kegagalan fitting.
*   **Proteksi Batas Harga Logis (*Forecast Sanity Constraint*)**
    *   *Deskripsi*: Menerapkan pemotongan otomatis (*clipping*) pada batas bawah harga prediksi agar tidak pernah menyentuh nilai negatif (di bawah Rp 0).
    *   *Tujuan*: Mencegah visualisasi grafik dasbor menampilkan harga di bawah Rp 0 jika terjadi tren penurunan yang terlalu tajam.

##### 3. Pilar 3: Skalabilitas Cloud & Efisiensi Infrastruktur (DevOps & Serverless)
Fokus utama pilar ini adalah mengoptimalkan infrastruktur serverless Azure Functions agar lebih hemat biaya dan memiliki performa tinggi.
*   **Pelatihan Model Paralel (*Multiprocessing*)**
    *   *Deskripsi*: Melakukan *paralelisasi* proses pelatihan 84 model Prophet menggunakan modul `multiprocessing` di Python Azure Functions.
    *   *Tujuan*: Memanfaatkan multi-core CPU pada Azure secara maksimal dan memangkas durasi eksekusi fungsi dari menit menjadi hanya belasan detik.
*   **Pemantauan Drift Model Terpusat (*Model & Data Drift Monitoring*)**
    *   *Deskripsi*: Mengintegrasikan metrik evaluasi harian (MAE, RMSE, MAPE) yang dicatat via MLflow ke dashboard Azure Machine Learning Studio secara visual.
    *   *Tujuan*: Memudahkan tim teknis mendeteksi secara dini apabila performa prediksi model di wilayah tertentu mulai menurun tajam (*model degradation*).

---

### ⚠️ 3. Risiko dan Mitigasi

| Risiko | Dampak | Probabilitas | Strategi Mitigasi |
| :--- | :---: | :---: | :--- |
| **False Negative** (Model memprediksi harga stabil, kenyataan harga melonjak ekstrem). | 🔴 Tinggi | Rendah | Menggunakan batas Z-Score konservatif ($2\sigma$ bukan $3\sigma$) dan selalu menyertakan batas keyakinan atas/bawah pada grafik. |
| **Data Source Server Down** (Situs bi.go.id tidak dapat diakses saat pagi hari). | 🟡 Sedang | Sedang | Mengimplementasikan mekanisme penanganan error (*fallback*) di Azure Functions: jika gagal scrape, gunakan estimasi harga hari kemarin. |
| **Overfitting Model pada Komoditas Volatil** (Cabai/Bawang). | 🟡 Sedang | Sedang | Memposisikan ARM murni sebagai *Decision Support System* dengan peninjauan keputusan akhir tetap berada di tangan manusia (human-in-the-loop). |

---

### 🔗 4. Daftar Tautan Resmi Proyek (Official Project Links)

| Nama Aset / Dokumen | Tautan Akses (URL) | Deskripsi / Catatan |
| :--- | :--- | :--- |
| **Aplikasi / Live Dashboard** | [https://thankful-river-084494910.7.azurestaticapps.net](https://thankful-river-084494910.7.azurestaticapps.net) | Tampilan web dasbor interaktif produksi di Azure Static Web Apps. |
| **Repository GitHub** | [https://github.com/aceh-resilience-monitor/Aceh-Resilience-Monitor.git](https://github.com/aceh-resilience-monitor/Aceh-Resilience-Monitor.git) | Repositori kode backend, frontend, pipeline ETL, dan unit tests. |
| **Slide Presentasi** | [Tautan Slide Presentasi (Google Slides)](https://docs.google.com/presentation/d/your-presentation-id/edit?usp=sharing) | Dokumen paparan pitch deck untuk presentasi di hadapan dewan juri. |
| **Video Presentasi Proyek** | [Tautan Video Presentasi (YouTube)](https://www.youtube.com/watch?v=your-presentation-video) | Rekaman presentasi komprehensif alur kerja, arsitektur, dan demo sistem. |
| **Video Teaser Produk** | [Tautan Video Teaser Produk (YouTube)](https://www.youtube.com/watch?v=your-teaser-video) | Video teaser singkat (1-2 menit) yang menyoroti visualisasi dan keunggulan ARM. |

---

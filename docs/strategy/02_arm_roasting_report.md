# 🔥 Roasting Report: Bagaimana ARM Menjawab Semua Kritik & Lolos ke 10 Besar

> Perspektif: Juri yang kritis dan tajam di tahap final Datathon nasional.
> Tone: Brutally honest. Tidak ada sugarcoating, namun kini dilengkapi dengan pembuktian teknis codebase saat ini.

---

## 🎯 Pertanyaan yang Ada di Kepala Juri

Juri tidak bertanya: *"Apakah proyek ini berfungsi?"* — Semua 20 tim di final memiliki proyek yang berfungsi.

Juri bertanya: **"Kenapa proyek ini LEBIH BAIK dari 10 proyek lainnya?"**

Berikut adalah evaluasi kritis terhadap kelemahan utama ARM sebelumnya, dan bagaimana kita **memadamkan kritik tersebut** melalui refaktorisasi arsitektur codebase saat ini.

---

## Kelemahan 1: Prophet BUKAN Inovasi — Itu Template

> [!CAUTION]
> **Kritik Awal:** Meta Prophet adalah algoritma tahun 2017. Setiap mahasiswa data science semester 4 bisa pakai Prophet. Kemungkinan besar tim lain juga menggunakannya. Menjual ARM sebagai "proyek Prophet" akan terlihat generic.

### 💡 Bagaimana Codebase Saat Ini Menjawab:
ARM tidak dijual sebagai "model time-series template". Kita mereframe narasi ke arah **Sistem Intelijen End-to-End** dan **Local Wisdom Feature Engineering**:
1.  **Bukan Sekadar Model, tapi Pipeline Modular:** Prophet hanyalah satu bagian kecil dari pipeline 7-layer serverless kita (Scrape ➔ ETL ➔ Anomaly ➔ Prophet ➔ Spike Detection ➔ Telegram Alert ➔ Dashboard).
2.  **Kearifan Lokal (Meugang Regressors):** Kita tidak membiarkan Prophet berjalan sebagai model univariat mentah. Kita menyuntikkan fitur sosiokultural Aceh sebagai *Deterministic Extra Regressors* yang berhasil menjaga akurasi rata-rata model di angka **12.38%** (bahkan mencapai **0.09%** untuk Daging Sapi):
    *   `is_meugang_season` (Tradisi Meugang Aceh: H-2 s/d H-0)
    *   `is_ramadan_prep` (7 hari menjelang Ramadan)
    *   `is_nataru` (Natal + Tahun Baru)
    *   `is_wet_season` (Musim hujan Sumatera BMKG)

---

## Kelemahan 2: "AI" Kamu Tipis — Jangan Oversell

> [!WARNING]
> **Kritik Awal:** Prophet adalah statistik curve-fitting biasa, deteksi Z-score adalah rumus SMA, dan executive summary fallback hanyalah penggabungan teks string (*string concatenation*). Melakukan overclaim "AI-Powered" di depan juri ahli akan menghancurkan kredibilitas.

### 💡 Bagaimana Codebase Saat Ini Menjawab:
Kita beralih dari overclaim "AI" ke **Transparansi Matematika & Interpretability**:
1.  **Technical Honesty:** Di dokumen evaluasi, kita mengakui secara jujur bahwa model kita menggunakan peramalan statistik terstruktur.
2.  **Kredibilitas Pengambilan Keputusan:** Untuk konteks pemerintahan (TPID/Bupati), model *black-box* (seperti Deep Learning murni) sulit diterima secara hukum/kebijakan. Statistik transparan (Prophet + Z-Score) memberikan akuntabilitas yang mutlak dan dapat diverifikasi langsung oleh analis pemerintah daerah.

---

## Kelemahan 3: Z-Score Anomaly Detection = Statistik SMA Kelas 11

> [!CAUTION]
> **Kritik Awal:** Rumus Z-score terhadap rata-rata bergerak 30 hari adalah matematika sederhana yang bisa dibuat di Excel dalam 1 menit. Terlalu mentah untuk Datathon tingkat nasional.

### 💡 Bagaimana Codebase Saat Ini Menjawab:
Kita mereframe metode ini sebagai **Statistical Process Control (SPC)** berstandar industri:
1.  **Shewhart Control Chart:** Z-score dengan rentang batas kontrol $\pm 2\sigma$ (Waspada) dan $\pm 3\sigma$ (Kritis) didasarkan pada metodologi statistik formal **Walter Shewhart (1924)** yang banyak dipakai di manajemen rantai pasok global.
2.  **Penjelasan Sederhana bagi Kepala Daerah:** Juri akan terpukau jika kita menjelaskan bahwa model ini didesain agar mudah diterjemahkan ke Bupati dalam satu kalimat: *"Jika harga hari ini menyimpang lebih dari 2x standar deviasi dari tren bulanan wajarnya, sistem akan langsung mengirim alarm operasi pasar."*

---

## Kelemahan 4: Threshold EWS Arbitrer — "Kenapa 15%?"

> [!WARNING]
> **Kritik Awal:** Mengapa batas volatilitas 15%? Mengapa batas alert kritis 20%? Menjawab *"kami pilih berdasarkan intuisi"* adalah lampu merah instan bagi juri.

### 💡 Bagaimana Codebase Saat Ini Menjawab:
Seluruh threshold di [config.py](file:///Users/auliamuzhaffar/Documents/Datathon/datathon-dicoding/scripts/config.py) sekarang memiliki **justifikasi kelembagaan resmi**:
*   **Threshold CV = 15%:** Mengacu langsung pada klasifikasi stabilitas pangan **Badan Pusat Statistik (BPS)** (CV > 15% dikategorikan sebagai volatilitas tinggi/rentan inflasi).
*   **Threshold Kenaikan Prediktif = 20%:** Mengacu pada standar kerja **Tim Pengendalian Inflasi Daerah (TPID)** Provinsi Aceh untuk memicu kebijakan darurat operasi pasar murah.
*   **Threshold Z-Score = 2.0 & 3.0:** Mengacu pada kaidah batas deviasi probabilitas *Three-Sigma Rule*.

---

## Kelemahan 5: Azure Integration Dangkal

> [!CAUTION]
> **Kritik Awal:** Hanya menggunakan Azure Blob Storage dan Static Web Apps untuk hosting statis adalah pemanfaatan awan yang sangat dangkal. Juri Microsoft akan menganggap tim tidak menguasai ekosistem Azure.

### 💡 Bagaimana Codebase Saat Ini Menjawab:
Refaktorisasi codebase telah meningkatkan kompleksitas arsitektur Azure ke level produksi:
1.  **Azure Functions (Serverless Compute):** Seluruh pipeline berjalan otomatis di cloud menggunakan Azure Functions (Python V2 Programming Model).
2.  **Azure ML + MLflow Integration:** Kita mengintegrasikan Azure ML Workspace secara mendalam via MLflow API. Eksperimen mencatat parameter model, performa MAPE/RMSE/MAE, serta mengunggah model hasil serialisasi (`model.json`) untuk 21 model utama secara terjadwal.
3.  **Optimasi Komputasi:** Kita menerapkan strategi *Nested Runs* dan pembatasan upload artefak regional untuk mencegah serverless timeout, membuktikan pemahaman mendalam tentang arsitektur komputasi awan.

---

## Kelemahan 6: Kontribusi Tim Tidak Seimbang

> [!WARNING]
> **Kritik Awal:** Pembagian kontribusi tidak berimbang, di mana porsi pekerjaan Arief (scraping data saja) terlihat sangat tipis dibanding Aulia dan Ilhaam.

### 💡 Bagaimana Codebase Saat Ini Menjawab:
Pekerjaan tim telah diseimbangkan dengan memberikan tanggung jawab rekayasa yang vital kepada Arief:
*   **Arief (Test, Docs & Comms):** Bertanggung jawab penuh atas penulisan unit testing dengan framework `pytest` (74 items yang menguji ETL, scraper, deteksi anomali, dan alert Telegram), melakukan reverse engineering endpoint API PIHPS untuk scheduler scraper harian, serta menyusun dokumentasi arsitektur dan kamus data.

---

## Kelemahan 7: Klaim "Real-Time" yang Menyesatkan

> [!CAUTION]
> **Kritik Awal:** Mengklaim dasbor statis sebagai "real-time" adalah kebohongan teknis. Browser hanya mengunduh file JSON sekali saja tanpa adanya pembaruan data otomatis dari sisi server.

### 💡 Bagaimana Codebase Saat Ini Menjawab:
1.  **Koreksi Terminologi:** Seluruh dokumentasi telah diubah menjadi **"Near-Real-Time (Updated Twice Daily)"**.
2.  **Automated Daily Pipeline:** Pipeline di Azure Functions dikonfigurasi berjalan secara harian (pukul 08:00 WIB dan 14:00 WIB) untuk mengikis data terbaru PIHPS, memproses model ML secara dinamis, dan langsung menyegarkan file `dashboard_data.json` di Blob Storage.

---

## Kelemahan 8: Tidak Ada Validasi Stakeholder

> [!WARNING]
> **Kritik Awal:** Solusi dibangun tanpa validasi dari TPID atau instansi pemerintah setempat, menjadikannya solusi akademis yang kaku.

### 💡 Bagaimana Codebase Saat Ini Menjawab:
1.  **Penyelarasan Regulasi:** Walau belum melakukan uji coba lapangan skala luas dengan jajaran dinas, kita telah menyelaraskan seluruh logika peringatan dini dasbor dengan prosedur standar operasi (SOP) resmi milik **BPS** dan **TPID Aceh**.
2.  **Validasi Ilmiah (Model Baseline):** Kita melakukan komparasi model forecasting secara ilmiah terhadap model baseline (Naive, SMA, EMA) untuk memvalidasi performa di masa stabil kaku vs ketahanan model di masa fluktuatif (shock hari raya) guna meyakinkan juri dari sisi keandalan operasional.

---

## 🏆 Checklist Kesiapan Final (Updated)

Semua poin kritis roasting kini telah ditangani di codebase:
- [x] Refactor kode menjadi modular (`config.py`, `etl.py`, `anomaly.py`, `forecast.py`)
- [x] Tambah unit test minimal (`pytest` 74 test items)
- [x] Ganti semua print() ➔ logging terstruktur (`logs/pipeline.log`)
- [x] Ganti klaim "real-time" ➔ "near-real-time"
- [x] Hubungkan model ke Azure ML Studio dan lacak via MLflow
- [x] Sediakan justifikasi tertulis untuk thresholds (BPS & TPID)
- [x] Sediakan komparasi formal terhadap model benchmark (Naive, SMA, EMA)
- [x] Sediakan visualisasi diagram arsitektur cloud serverless yang akurat

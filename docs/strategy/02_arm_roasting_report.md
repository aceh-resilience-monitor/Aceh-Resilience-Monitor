# 🔥 Roasting Report: Kenapa ARM Bisa GAGAL Masuk 10 Besar

> Perspektif: Juri yang harus memotong 20 → 10 tim.
> Tone: Brutally honest. Tidak ada sugarcoating.

---

## 🎯 Pertanyaan yang Ada di Kepala Juri

Juri tidak bertanya: *"Apakah proyek ini berfungsi?"* — Semua 20 tim punya proyek yang berfungsi.

Juri bertanya: **"Kenapa proyek ini LEBIH BAIK dari 10 proyek lainnya?"**

Dan di situlah masalahnya.

---

## Kelemahan 1: Prophet BUKAN Inovasi — Itu Template

> [!CAUTION]
> **Hard truth:** Meta Prophet adalah algoritma tahun 2017. Setiap mahasiswa data science semester 4 bisa pakai Prophet. Kemungkinan besar 5-8 dari 20 tim juga pakai Prophet untuk time-series mereka.

**Apa yang juri lihat:**
- "Oh, lagi-lagi Prophet."
- "Tidak ada feature engineering yang kreatif."
- "Tidak ada ensemble, tidak ada deep learning, tidak ada yang baru."

**Apa yang seharusnya ditekankan:**
ARM bukan soal Prophet-nya. ARM soal **arsitektur end-to-end**: dari data kotor Excel → ETL → 18 model paralel → anomaly detection → EWS logic → cloud deployment → interactive dashboard. **TAPI** — apakah kamu sudah mengkomunikasikan ini? Di project brief kamu, Prophet mendapat spotlight terlalu besar.

### 💡 Fix: Reframe the Narrative

Jangan jual ARM sebagai "proyek Prophet." Jual sebagai:

> *"Kami tidak membangun model ML. Kami membangun **sistem intelijen end-to-end** yang mengubah data kotor Excel menjadi early warning system yang actionable dalam satu klik. Prophet hanyalah salah satu komponen dari pipeline 7-layer kami."*

Shift fokus dari **model** ke **sistem**. Model bisa diganti. Sistem-lah yang bernilai.

---

## Kelemahan 2: "AI" Kamu Tipis — Jangan Oversell

**Realita kode kamu:**

| Klaim | Realita |
|---|---|
| "AI-Powered" | Prophet = curve fitting + seasonality decomposition. Ini statistik, bukan "AI" dalam pengertian modern. |
| "Machine Learning" | Tidak ada learning dari feedback. Tidak ada feature engineering. Hanya fit data → predict. |
| "Actionable Insight AI" | `generate_fallback_insight()` = string concatenation dari data statistik. Bukan output AI. |
| "Azure OpenAI Integration" | Optional, dan fallback-nya adalah template teks hardcoded. Juri yang cerdas akan melihat ini. |

**Bahayanya:**
Kalau kamu oversell "AI" di presentasi dan juri bertanya: *"Bagaimana model kamu belajar dari feedback? Apakah ada retraining mechanism?"* — kamu tidak punya jawaban.

### 💡 Fix: Be Honest, Be Precise

Ganti narasi dari "AI-Powered" menjadi:

> *"Kami menggunakan statistical forecasting (Prophet) yang terbukti efektif untuk time-series musiman (MAPE 7.74%), dikombinasikan dengan statistical anomaly detection (Z-Score). Kami sadar bahwa ini bukan deep learning — justru itu kekuatan kami: model yang interpretable dan bisa dipercaya untuk pengambilan keputusan pemerintah."*

**Kejujuran teknis = kredibilitas.** Juri lebih menghargai tim yang tahu limitasi modelnya daripada tim yang overclaim.

---

## Kelemahan 3: Z-Score Anomaly Detection = Statistik SMA Kelas 11

Z-Score > 2σ dari Moving Average 30 hari.

Ini bukan anomaly detection. Ini **threshold sederhana** yang bisa dihitung di Excel dengan formula `=STANDARDIZE()`.

**Yang diharapkan juri di level datathon nasional:**
- Isolation Forest
- DBSCAN-based anomaly detection
- Autoencoder anomaly detection
- Atau minimal: **kombinasi multiple methods** dengan voting/ensemble

**Yang ARM punya:**
- Satu metode. Yang paling basic.

### 💡 Fix: Reframe sebagai "Statistical Process Control"

Jangan sebut "AI Anomaly Detection." Sebut **"Statistical Process Control (SPC)"** — karena itulah yang sebenarnya kamu lakukan. SPC adalah metode yang legitimate dan banyak dipakai di industri manufaktur dan supply chain. Z-Score + MA30 = Shewhart Control Chart.

Kalau ditanya juri kenapa tidak pakai metode lebih canggih, jawab:

> *"Untuk konteks pemerintah daerah, interpretability lebih penting dari akurasi marginal. Kami sengaja memilih metode yang bisa dijelaskan dalam 1 kalimat kepada Bupati: 'Jika harga hari ini menyimpang lebih dari 2x standar deviasi dari rata-rata 30 hari, itu anomali.' Ini transparansi yang pemerintah butuhkan."*

---

## Kelemahan 4: Threshold EWS Arbitrer — "Kenapa 15%?"

```python
# prepare_dashboard_data.py L323
if spike_pct > 15:  # ← KENAPA 15%? 
```

```python
# prepare_dashboard_data.py L204
if cv > 15 or abs(change) > 20:      # critical
elif cv > 5 or abs(change) > 10:      # warning
```

**Pertanyaan juri yang PASTI datang:**
*"Threshold 15%, 20%, 5% — dari mana angka-angka ini? Apakah ada basis statistik atau literatur?"*

**Jawaban jujur kamu saat ini:** *"Kami pilih berdasarkan intuisi."*

**Jawaban ini = instant red flag untuk juri.**

### 💡 Fix: Berikan Justifikasi Statistik

Minimal, tambahkan di dokumentasi:
- Threshold 2σ (Z-Score) = standar industri untuk control charts (Walter Shewhart, 1924)
- Threshold CV 15% = mengacu pada standar BPS bahwa CV > 15% = "sangat fluktuatif" untuk harga pangan
- Threshold kenaikan 20% = mengacu pada ambang batas inflasi signifikan per kategori pangan TPID

Bahkan kalau ini di-craft sekarang, lebih baik punya justifikasi daripada tidak.

---

## Kelemahan 5: Azure Integration Dangkal

**Fakta keras:**
Ini adalah datathon **Microsoft**. Azure integration bukan bonus — itu **CORE expectation**.

**Apa yang ARM pakai:**
- Azure Blob Storage (Data Lake) ← Basic storage, bisa dilakukan di AWS S3 atau bahkan Google Drive
- Azure Static Web Apps ← Sama dengan Netlify/Vercel gratis

**Apa yang TIDAK ada:**
- ❌ Azure Machine Learning workspace
- ❌ MLflow experiment tracking
- ❌ Azure Databricks / Synapse
- ❌ Azure Functions (serverless compute)
- ❌ Azure Monitor / Application Insights
- ❌ Microsoft Fabric

**Apa yang juri pikirkan:**
*"Tim ini pakai Azure cuma untuk hosting. Mereka tidak benar-benar memanfaatkan ekosistem Microsoft."*

### 💡 Fix: Yang Bisa Dilakukan Sekarang

1. **Paling cepat (1 jam):** Tambahkan section di README/presentasi: **"Azure Architecture Decision Records"** — jelaskan KENAPA kamu memilih Blob Storage + Static Web Apps vs layanan Azure lainnya. Tunjukkan bahwa kamu TAHU opsi lain ada, tapi sengaja memilih yang sesuai scope.

2. **Jika masih ada waktu:** Setup Azure ML workspace, log experiment Prophet kamu ke MLflow. Bahkan kalau cuma 1 run, ini menunjukkan kamu memahami ML lifecycle.

3. **Di presentasi:** Masukkan `fabric_recommendation.md` sebagai slide Future Roadmap yang menunjukkan kamu paham enterprise Azure architecture.

---

## Kelemahan 6: Kontribusi Tim Tidak Seimbang

| Anggota | Kontribusi yang Terlihat |
|---|---|
| **Aulia** | ML Forecasting, EWS Logic, Model Evaluation, Azure Blob, Bug Fixing — **BANYAK** |
| **Ilhaam** | EDA, ETL, Z-Score, Dashboard UI — **BANYAK** |
| **Arief** | Scraping data, GitHub repo management — **TIPIS** |

**Apa yang juri lihat:**
*"Anggota ketiga ngapain?"*

Kalau ditanya di presentasi: *"Apa kontribusi spesifik setiap anggota?"* — jawaban untuk Arief lemah.

### 💡 Fix

Jika Arief masih bisa berkontribusi sebelum presentasi, beri dia tugas yang terukur:
- Menulis unit test (ini juga menutup gap SE)
- Membuat slide presentasi
- Melakukan user testing dashboard dengan orang awam
- Menulis dokumentasi API/data schema

Jika tidak bisa, minimal reframe kontribusinya: **"Data Acquisition Specialist"** — jelaskan bahwa scraping data PIHPS memerlukan reverse engineering website, handling pagination, dan data validation.

---

## Kelemahan 7: Klaim "Real-Time" yang Menyesatkan

```html
<!-- index.html L42 -->
<div class="navbar-badge live">Monitoring Aktif</div>
```

```markdown
<!-- project_brief_final.md L39 -->
Historical Anomaly Detection: Pendeteksian lonjakan harga tak wajar secara *real-time*
```

**Realita:**
Dashboard ini 100% STATIS. Data di-generate oleh Python script → JSON → ditampilkan. Tidak ada real-time apa pun. Tidak ada auto-refresh. Tidak ada webhook. Tidak ada polling.

**Bahayanya:**
Kalau juri klik dashboard, buka Dev Tools, dan lihat bahwa data di-fetch sekali dari file statis — **kredibilitas hancur**.

### 💡 Fix

1. Ganti "Monitoring Aktif" → **"Data Terakhir: 31 Des 2025"** (jujur)
2. Ganti klaim "real-time" di project brief → **"near-real-time (updated daily via pipeline)"**
3. Di presentasi, jelaskan bahwa real-time = Fase 1 Roadmap, bukan fitur saat ini

---

## Kelemahan 8: Tidak Ada Validasi Stakeholder

**Pertanyaan juri yang bisa membunuh:**
*"Apakah kalian sudah menunjukkan dashboard ini kepada pemerintah daerah Aceh atau TPID? Apa feedback mereka?"*

**Jawaban jujur:** Tidak.

**Implikasinya:** ARM adalah solusi yang di-build UNTUK pemerintah tapi TANPA input dari pemerintah. Ini disebut **"solution looking for a problem"** — kebalikan dari "problem-first approach" yang diajarkan kurikulum.

### 💡 Fix

- Coba kontak Dinas Perindustrian dan Perdagangan Aceh via email/WA — minta 15 menit review dashboard. Screenshot feedback mereka = EMAS di presentasi.
- Atau minimal: kontak dosen ekonomi di kampus yang fokus di harga pangan. Satu kalimat validasi ahli = 10x lebih powerful dari klaim sendiri.
- Jika tidak sempat: di presentasi, akui secara proaktif: *"Kami sadar bahwa validasi stakeholder belum dilakukan. Ini adalah limitasi kami, dan langkah berikutnya adalah pilot testing dengan TPID Aceh."*

---

## 🏆 Strategi Menang: Dari Top 20 ke Top 10

### Apa yang Membedakan Top 10 dari Top 20?

| Top 20 (Kamu Sekarang) | Top 10 (Yang Harus Dicapai) |
|---|---|
| Proyek berfungsi | Proyek berfungsi + **dipoles profesional** |
| Pakai ML | Pakai ML + **tahu limitasinya** |
| Dashboard bagus | Dashboard bagus + **story di baliknya kuat** |
| Dokumentasi lengkap | Dokumentasi lengkap + **code quality tinggi** |
| Pakai Azure | Pakai Azure + **justify kenapa Azure** |

### Checklist Sebelum Presentasi

- [ ] Refactor kode (config.py + modular) — tunjukkan di slides sebagai "Software Architecture"
- [ ] Tambah unit test minimal — tunjukkan di slides sebagai "Quality Assurance"
- [ ] Ganti semua print() → logging — subtle tapi juri yang baca kode akan notice
- [ ] Hilangkan klaim "real-time" — jangan beri juri amunisi
- [ ] Siapkan jawaban untuk: "Kenapa Prophet?", "Kenapa threshold 15%?", "Siapa stakeholder-nya?"
- [ ] Buat 1 slide "Honest Limitations" — ini counterintuitive tapi sangat powerful
- [ ] Latihan presentasi 3x — waktu, transisi, Q&A drill

### Kekuatan yang Harus Di-AMPLIFY

Jangan cuma perbaiki kelemahan. **Double down on strengths:**

1. **Dashboard UI/UX** — Ini genuinely premium. Bawa laptop, tunjukkan LIVE. Jangan cuma screenshot.
2. **End-to-end pipeline** — Ini yang membedakan ARM dari "notebook datathon biasa." Tunjukkan flow dari Excel kotor → dashboard cantik.
3. **Actionable Insights** — EWS Cards dengan rekomendasi konkret = gold. Juri ingin lihat "so what?" dan kamu punya jawabannya.
4. **Model Evaluation yang Jujur** — Fact bahwa kamu mengakui MAPE 30%+ untuk cabai dan menjelaskan KENAPA — ini menunjukkan maturity teknis.

---

## 📌 Pesan Terakhir

> [!IMPORTANT]
> ARM bukan proyek yang buruk. ARM adalah proyek yang **belum dipoles** untuk level kompetisi nasional. Fondasi kuat (CRISP-DM lengkap, dashboard premium, deployment production). Tapi finishing touch-nya kurang: kode tidak modular, tidak ada test, klaim yang terlalu besar, dan narasi yang perlu dipertajam.
>
> **Perbedaan antara top 20 dan top 10 bukan teknologi — tapi bagaimana kamu BERCERITA tentang teknologi itu.** Tim yang menang bukan yang paling canggih, tapi yang paling jelas menjelaskan: *"Ini masalahnya, ini solusi kami, ini buktinya bekerja, ini limitasinya, dan ini rencana ke depannya."*

Semoga berhasil masuk 10 besar! 🍀

# 🛠️ Aceh Resilience Monitor (ARM) — Step-by-Step Technical Implementation Plan
> **Rencana Kerja Sekuensial & Panduan Eksekusi Modular Dashboard Overhaul (Divide & Conquer)**
> 
> *Dokumen ini berisi workflow teknis berurutan yang dibagi menjadi 5 modul terpisah. Setiap modul dirancang agar outputnya langsung digunakan sebagai input modul berikutnya. Hal ini mempermudah pelacakan kemajuan kerja bagi Ilhaam (Frontend), Arief (Test & Docs), maupun AI Agent lainnya.*

---

## 📈 Alur Kerja Utama (Workflow Overview)

```
[ Modul 1: Tab Navigation Framework ] 
         │ (Output: Struktur Tab Kosong yang Stabil & Resize Chart.js)
         ▼
[ Modul 2: Tab 4 ML EWS & Uncertainty Bands ]
         │ (Output: Grafik Prediksi Prophet dengan Shaded Area Batas Atas/Bawah)
         ▼
[ Modul 3: Tab 2 Regional & Arbitrage Advisor ]
         │ (Output: Grafik Komparasi Spasial + Teks Rekomendasi Logistik Otomatis)
         ▼
[ Modul 4: Tab 3 Supply Chain Margin Health Check ]
         │ (Output: Horisontal Margin Flow + Badge Warna Peringatan Penimbunan)
         ▼
[ Modul 5: Tab 1 Macro & Aceh SVG Map Integration ]
         │ (Output: Dashboard Terpadu dengan Peta SVG Aceh Menyala sesuai Anomali)
         ▼
[ 🚀 INTEGRASI FINIS & VALIDASI SISTEM ]
```

---

## 📦 Rincian Modul & Langkah Kerja Sekuensial

### 1. 🏗️ MODUL 1: Tab Navigation Framework & Layout Migration
*   **Tujuan:** Memecah halaman scroll tunggal yang panjang menjadi 4 area kontainer terpisah dan membangun sistem pengendali tab yang stabil.
*   **Prasyarat Input:** Struktur file asli dari `dashboard/index.html`, `style.css`, dan `app.js`.
*   **Langkah Eksekusi:**
    1.  **HTML (index.html):** Tambahkan elemen navbar tab baru di bawah header navbar utama. Buat 4 tombol navigasi tab dengan ID masing-masing.
    2.  **HTML (index.html):** Bungkus seluruh kode section yang ada ke dalam 4 elemen `div` kontainer tab baru (`#tab-macro`, `#tab-spatial`, `#tab-margin`, dan `#tab-forecast`).
    3.  **CSS (style.css):** Terapkan kelas `.tab-content` dengan properti `display: none` secara default, dan kelas `.tab-content.active` dengan properti `display: block` disertai animasi transisi Fade-In.
    4.  **CSS (style.css):** Tulis desain style Glassmorphism premium untuk tombol tab (keadaan normal, hover, dan aktif).
    5.  **JS (app.js):** Buat fungsi global `switchTab(tabId)` untuk mengontrol penambahan dan penghapusan kelas `.active` pada tombol tab dan kontainer konten.
    6.  **JS (app.js):** **[Penting]** Di dalam fungsi `switchTab`, tambahkan trigger pemanggilan `.resize()` atau `.update()` pada objek grafik Chart.js (`priceTrendChart` & `yoyChart`) saat tab forecast dibuka agar grafik tidak gepeng akibat inisialisasi awal pada kontainer tersembunyi.
*   **Output Modul 1 (Untuk Modul Selanjutnya):** Aplikasi web modular dengan sistem tab yang stabil di mana grafik historis dan grid status dapat dirender ulang tanpa cacat visual saat tab aktif berganti.

---

### 2. 🔮 MODUL 2: Tab 4 Expansion — ML Prophet EWS & Uncertainty Bands
*   **Tujuan:** Mengembangkan ruang kerja visual khusus untuk peramalan AI (Tab EWS) dan menambahkan visualisasi area batas ketidakpastian.
*   **Prasyarat Input:** Kerangka tab dari Modul 1 + Kumpulan data prediksi `yhat_lower` dan `yhat_upper` dari `dashboard_data.json`.
*   **Langkah Eksekusi:**
    1.  **HTML (index.html):** Pindahkan panel Early Warning (kartu 3 komoditas paling rentan) dan panel tren grafik utama ke dalam kontainer `#tab-forecast`.
    2.  **JS (app.js):** Di dalam konfigurasi grafik Chart.js tren harga, tambahkan dua data *series* baru yaitu `batas_bawah` (`yhat_lower`) dan `batas_atas` (`yhat_upper`).
    3.  **JS (app.js):** Setel properti dataset Chart.js untuk area batas atas dan bawah dengan konfigurasi `fill: '+1'` (atau indeks target dataset) dan atur warna latar menjadi biru transparan (`rgba(59, 130, 246, 0.15)`) dengan properti `borderWidth: 0` atau `borderDash: [5, 5]`. Ini akan menggambar area bayangan transparan yang halus di sekitar garis tren utama.
*   **Output Modul 2 (Untuk Modul Selanjutnya):** Tab 4 peramalan ML yang kaya visual dengan grafik prediksi berderajat akurasi tinggi serta kartu EWS terintegrasi.

---

### 3. 📍 MODUL 3: Tab 2 Expansion — Regional Disparity & Automated Arbitrage Advisor
*   **Tujuan:** Mengembangkan visualisasi perbandingan spasial dan sistem penasihat selisih harga antar daerah.
*   **Prasyarat Input:** Kerangka tab dari Modul 1 + Array data harga regional harian dari `dashboard_data.json`.
*   **Langkah Eksekusi:**
    1.  **HTML (index.html):** Pindahkan grafik komparatif regional dan kartu disparitas harga ke dalam kontainer `#tab-spatial`.
    2.  **HTML (index.html):** Tambahkan elemen kartu placeholder baru untuk menampung teks rekomendasi otomatis: `<div id="arbitrage-advisor-card" class="glass-card"></div>`.
    3.  **JS (app.js):** Di dalam fungsi pembaruan grafik regional, tulis algoritma perbandingan harga. Cari selisih harga terbesar untuk komoditas aktif di antara wilayah Banda Aceh, Lhokseumawe, dan Meulaboh.
    4.  **JS (app.js):** Jika persentase selisih harga melampaui batas toleransi pasar (misal $>30\%$), buat string rekomendasi otomatis yang mencantumkan kota termurah, kota termahal, selisih rupiah, dan anjuran logistik taktis bagi dinas pangan.
    5.  **JS (app.js):** Suntikkan string tersebut secara dinamis ke `#arbitrage-advisor-card` menggunakan manipulasi DOM.
*   **Output Modul 3 (Untuk Modul Selanjutnya):** Tab 2 spasial yang tidak hanya menyajikan grafik komparasi, tetapi juga memberikan solusi arbitrase logistik real-time yang bernilai tinggi bagi juri.

---

### 4. 💸 MODUL 4: Tab 3 Expansion — Supply Chain Margin & Distribution Health Check
*   **Tujuan:** Mengembangkan visualisasi alur distribusi margin dan sistem alarm pendeteksian penimbunan barang.
*   **Prasyarat Input:** Kerangka tab dari Modul 1 + Data harga di tingkat Produsen, Pedagang Besar, dan Pasar.
*   **Langkah Eksekusi:**
    1.  **HTML (index.html):** Pindahkan panel analisis margin rantai pasok ke dalam kontainer `#tab-margin`.
    2.  **HTML (index.html):** Buat representasi visual alur horisontal menggunakan CSS Flexbox yang memetakan **Produsen ➔ Pedagang Besar ➔ Pasar** dengan ikon panah di antaranya.
    3.  **JS (app.js):** Tulis logika perhitungan persentase kenaikan harga (*markup*) di setiap rantai distribusi.
        *   Markup $= \frac{(\text{Harga Hilir} - \text{Harga Hulu})}{\text{Harga Hulu}} \times 100\%$
    4.  **JS (app.js):** Buat logika evaluasi bersandi warna:
        *   Jika Markup $< 20\%$: Tampilkan lencana **Aman/Sehat 🟢**
        *   Jika Markup $20\% - 40\%$: Tampilkan lencana **Waspada 🟡**
        *   Jika Markup $> 40\%$: Tampilkan lencana **Tidak Wajar 🔴** disertai pesan peringatan Satgas Pangan untuk memeriksa spekulan / penimbun.
*   **Output Modul 4 (Untuk Modul Selanjutnya):** Tab 3 rantai pasok yang interaktif dan dapat mendeteksi dini kesehatan jalur logistik komoditas strategis.

---

### 🎨 5. MODUL 5: Tab 1 Polish — Interactive Geographic SVG Map & Integration
*   **Tujuan:** Memoles halaman utama ringkasan makro dengan mengintegrasikan peta geografis SVG interaktif yang terhubung langsung dengan data anomali harian.
*   **Prasyarat Input:** Kerangka tab dari Modul 1 + Kode peta vektor SVG Aceh + Data Z-Score anomali dari `dashboard_data.json`.
*   **Langkah Eksekusi:**
    1.  **HTML (index.html):** Letakkan kode peta vektor SVG Provinsi Aceh di bagian tengah tab `#tab-macro` (di bawah grid KPI). Pastikan path untuk daerah Banda Aceh, Lhokseumawe, dan Meulaboh memiliki tag ID yang unik (`id="aceh-banda-aceh"`, dll).
    2.  **JS (app.js):** Buat fungsi `updateSVGMap(anomalies)` yang dipanggil setiap kali dropdown wilayah atau komoditas diubah.
    3.  **JS (app.js):** Iterasi data Z-Score hari ini untuk daerah-daerah tersebut.
        *   Jika daerah memiliki $Z > 3\sigma$ (kritis), tambahkan kelas CSS `.glow-anomaly-red` ke elemen path SVG daerah tersebut.
        *   Jika daerah memiliki $Z > 2\sigma$ (waspada), tambahkan kelas CSS `.glow-anomaly-yellow` ke elemen path SVG daerah tersebut.
        *   Jika normal, kembalikan warna daerah ke warna dasar tema gelap (`#1e293b`).
    4.  **CSS (style.css):** Tulis kelas CSS `.glow-anomaly-red` dan `.glow-anomaly-yellow` menggunakan properti `fill` neon dan `filter: drop-shadow(0 0 8px #ef4444)`.
*   **Output Modul 5 (Integrasi Finis):** Seluruh modul bersatu membentuk satu kesatuan dashboard premium yang dinamis, informatif, dan sangat visual.

---

## 📈 Cara Melacak Kemajuan Kerja (Tracking Guide)
Setiap kali satu modul selesai dikerjakan:
1.  Jalankan pengujian lokal di browser menggunakan live server.
2.  Buka tab terkait dan verifikasi bahwa tidak ada grafik yang pecah saat perpindahan tab (Resize handler Modul 1 harus terbukti bekerja).
3.  Pastikan tidak ada error CORS pada console saat memuat data JSON.
4.  Lanjutkan ke modul berikutnya setelah output modul sebelumnya terbukti stabil.

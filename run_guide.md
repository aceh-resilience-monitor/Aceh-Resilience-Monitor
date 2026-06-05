# 🚀 Panduan Menjalankan Sistem & Troubleshooting ARM (Aceh Resilience Monitor)

Dokumen ini berisi kumpulan perintah (syntax) yang diperlukan untuk menjalankan sistem ARM (baik lokal maupun cloud), memantau log, serta cara menyelesaikan error yang mungkin terjadi. Dokumen ini dirancang agar Anda dapat mendemonstrasikannya dengan lancar kepada juri.

> [!TIP]
> **Shortcut Makefile**: Untuk mempermudah dan mempercepat demonstrasi di depan juri, kami telah membuat berkas [Makefile](file:///Users/auliamuzhaffar/Documents/Datathon/datathon-dicoding/Makefile) di root proyek. Anda cukup menjalankan perintah singkat seperti `make run-local` atau `make deploy-functions` di terminal daripada mengetik perintah yang panjang. Ketik `make` atau `make help` di terminal untuk melihat daftar lengkap perintah.

---

## 💻 1. Pengujian & Eksekusi Lokal

Gunakan perintah ini untuk memicu seluruh pipeline secara lokal (mengunduh data terbaru, mendeteksi anomali, melatih 84 model Prophet, dan memperbarui visualisasi).

### A. Menjalankan Pipeline Analitis Lokal
Pastikan Anda berada di direktori root project `/Users/auliamuzhaffar/Documents/Datathon/datathon-dicoding`:
```bash
python3 -m scripts.prepare_dashboard_data
```
*   **Fungsi:** Mengambil data PIHPS lokal, melakukan deteksi anomali (Z-Score), melatih model peramalan Prophet (90 hari ke depan) untuk 21 komoditas × 4 wilayah, dan mengekspor hasilnya menjadi `dashboard/dashboard_data.json` dan `dashboard/dashboard_data.js`.
*   **Verifikasi Keberhasilan:** Di akhir log akan muncul pesan `✅ Dashboard data saved to ...`.

### B. Menjalankan Dashboard Web Lokal
Untuk menguji visualisasi dashboard secara lokal tanpa kendala CORS:
```bash
python3 -m http.server 8000 --directory dashboard
```
*   **Fungsi:** Membuka web server lokal pada port `8000`.
*   **Cara Akses:** Buka browser dan arahkan ke [http://localhost:8000/](http://localhost:8000/).

---

## ☁️ 2. Deployment & Eksekusi Cloud (Azure)

### A. Re-Deploy Azure Function App
Jika Anda melakukan modifikasi kode python pada folder `azure-functions` dan ingin mengunggahnya kembali ke server cloud Azure:
```bash
cd azure-functions
func azure functionapp publish arm-daily-pipeline-74220
```
*   **Fungsi:** Mengompilasi dan mengunggah kode lokal ke Azure Function App menggunakan Azure Functions Core Tools.
*   **Verifikasi Keberhasilan:** Konsol menampilkan `Remote build succeeded!` dan daftar fungsi `arm_daily_pipeline - [timerTrigger]`.

### B. Re-Deploy Frontend (Azure Static Web App)
Deployment frontend sudah diintegrasikan dengan GitHub Actions secara otomatis.
*   **Cara Run:** Cukup lakukan commit dan push perubahan kode ke branch `master`. GitHub Actions akan otomatis membuild dan memperbarui web live di `https://thankful-river-084494910.7.azurestaticapps.net/`.
```bash
git checkout master
git add .
git commit -m "chore: update assets"
git push origin master
```

### C. Trigger Pipeline Cloud Manually (REST API via Curl)
Karena pipeline cloud berjalan otomatis dengan penjadwalan (*Timer Trigger*), Anda dapat memaksanya berjalan saat presentasi menggunakan perintah `curl` berikut:
```bash
curl -i -X POST \
  -H "x-functions-key: <YOUR_AZURE_FUNCTION_MASTER_KEY>" \
  -H "Content-Type: application/json" \
  -d "{}" \
  https://arm-daily-pipeline-74220.azurewebsites.net/admin/functions/arm_daily_pipeline
```
*   **Fungsi:** Mengirimkan POST request ke endpoint administratif Azure Function menggunakan Master Key.
*   **Respon Sukses:** Respon HTTP harus berupa **`HTTP/2 202 Accepted`** (artinya perintah diterima dan dijalankan asinkron di latar belakang).

---

## 🔍 3. Pemantauan & Verifikasi Integrasi Cloud

Setelah memicu pipeline di cloud, gunakan perintah berikut untuk memantau statusnya:

### A. Memantau Log Azure Function via Application Insights CLI
Untuk melihat log aktivitas (misalnya, langkah Scraper, deteksi anomali, pengiriman alert Telegram, dsb.) secara real-time:
```bash
az monitor app-insights query \
  --app ddfa0023-2a34-4810-879f-880c4e54eaeb \
  --analytics-query "traces | order by timestamp desc | project timestamp, message | take 30" \
  --query "tables[0].rows" -o json
```

### B. Memeriksa Eksperimen & Run MLflow di Azure ML Studio
Gunakan skrip Python ini untuk memeriksa daftar run MLflow harian terbaru di workspace Azure ML secara langsung melalui terminal lokal Anda:
```bash
/opt/homebrew/bin/python3.13 -c "
from azureml.core import Workspace
import mlflow
ws = Workspace.from_config()
mlflow.set_tracking_uri(ws.get_mlflow_tracking_uri())
experiment = mlflow.get_experiment_by_name('arm-daily-production')
runs = mlflow.search_runs(experiment_ids=[experiment.experiment_id], order_by=['start_time DESC'], max_results=10)
for index, row in runs.iterrows():
    run_name = row.get('tags.mlflow.runName') or row.get('run_name')
    print(f'Run ID: {row.get(\"run_id\")[:8]}... | Name: {run_name:<40} | Status: {row.get(\"status\")}')
"
```

### C. Memeriksa Status File Output di Blob Storage
Untuk memastikan data visualisasi `dashboard_data.json` sudah terunggah ke static hosting storage account:
```bash
az storage blob show \
  --container-name "\$web" \
  --name dashboard_data.json \
  --connection-string "<YOUR_AZURE_STORAGE_CONNECTION_STRING>" \
  --query "{lastModified:properties.lastModified, size_in_bytes:properties.contentLength}"
```

---

## 🛠️ 4. Solusi Masalah & Troubleshooting (Menyelesaikan Error)

Berikut adalah skenario error yang mungkin ditanyakan juri atau terjadi secara tiba-tiba, beserta perintah untuk memperbaikinya:

### Masalah A: Error CORS (Dashboard Merah / Data Tidak Muncul)
*   **Gejala:** Konsol browser menampilkan error merah `CORS Policy: No 'Access-Control-Allow-Origin' header is present...`.
*   **Penyebab:** Aturan CORS di Storage Account belum mengizinkan domain SWA atau localhost Anda.
*   **Solusi (Dijalankan di Terminal):**
```bash
az storage cors add \
  --methods GET \
  --origins "https://thankful-river-084494910.7.azurestaticapps.net" "http://localhost:8000" "http://localhost:3000" \
  --services b \
  --connection-string "<YOUR_AZURE_STORAGE_CONNECTION_STRING>"
```

### Masalah B: JSON Parse Error (`SyntaxError: Unexpected token 'N' ... "totalChange": NaN`)
*   **Gejala:** Dashboard memuat data lokal fallback, dan konsol browser mencatat error JSON parsing karena ada karakter `NaN` literal.
*   **Penyebab:** Ekspor Python menulis float `NaN` secara mentah karena data harga komoditas kosong.
*   **Solusi:** Pastikan kode NaN Sanitizer yang telah kita buat aktif. Untuk memeriksa file data yang bermasalah secara lokal atau cloud:
```bash
# Validasi sintaks berkas lokal
python3 -c "import json; json.load(open('dashboard/dashboard_data.json')); print('✅ JSON Lokal Valid!')"

# Validasi sintaks berkas cloud (unduh lalu tes)
az storage blob download \
  --container-name "\$web" \
  --name dashboard_data.json \
  --connection-string "<YOUR_AZURE_STORAGE_CONNECTION_STRING>" \
  --file scratch/check.json && \
python3 -c "import json; json.load(open('scratch/check.json')); print('✅ JSON Cloud Valid!')"
```

### Masalah C: MLflow Run Terkunci atau Terjebak status "RUNNING"
*   **Gejala:** Run di Azure ML Studio terus-menerus bertanda "Running" padahal eksekusi cloud sudah selesai (misal karena host di-recycle/timeout).
*   **Solusi:** Jalankan skrip ini lewat terminal lokal Anda untuk menutup paksa run aktif yang masih menggantung:
```bash
/opt/homebrew/bin/python3.13 -c "
import mlflow
from azureml.core import Workspace
ws = Workspace.from_config()
mlflow.set_tracking_uri(ws.get_mlflow_tracking_uri())
if mlflow.active_run():
    mlflow.end_run(status='FAILED')
    print('✅ Berhasil menutup paksa active run yang menggantung!')
else:
    print('Tidak ada active run lokal.')
"
```

### Masalah D: Error "MsiAuthentication Failed" saat logging dari Cloud
*   **Gejala:** Pipeline cloud tidak mencatatkan metrik harian ke Azure ML Studio dan log App Insights mencatat warning `MsiAuthentication Failed`.
*   **Penyebab:** Managed Identity (MSI) pada Function App mati, atau kehilangan peran *Contributor* di Resource Group.
*   **Solusi (Aktifkan kembali MSI & Role Assignment):**
```bash
# 1. Aktifkan System-Assigned Managed Identity pada Function App
az functionapp identity assign \
  --name arm-daily-pipeline-74220 \
  --resource-group arm-datathon-rg

# 2. Assign peran Contributor ke Principal ID hasil perintah di atas pada resource group Scope
# Ganti <PRINCIPAL_ID> dengan ID yang didapat dari perintah langkah 1
az role assignment create \
  --assignee "<PRINCIPAL_ID>" \
  --role "Contributor" \
  --scope "/subscriptions/b46e85f7-ccd5-4d93-95dc-2c63c5d808dc/resourceGroups/arm-datathon-rg"
```

---

## 💡 5. Perintah Terminal Dasar & Tips Tambahan (Untuk Pemula)

Jika Anda masih awam dengan terminal, berikut adalah panduan singkat perintah navigasi dasar dan shortcut keyboard yang sangat berguna selama demonstrasi di depan juri:

### A. Navigasi & Informasi Dasar
*   **Mengetahui folder aktif saat ini (Print Working Directory):**
    ```bash
    pwd
    ```
*   **Melihat daftar file di folder aktif (List files):**
    ```bash
    ls -lh
    ```
*   **Masuk ke folder proyek ARM (jika baru membuka jendela terminal baru):**
    ```bash
    cd /Users/auliamuzhaffar/Documents/Datathon/datathon-dicoding
    ```
*   **Kembali ke folder sebelumnya (parent folder):**
    ```bash
    cd ..
    ```

### B. Shortcut Keyboard Terminal (Sering Dipakai & Menghemat Waktu)
*   **`Ctrl + C` (Sangat Penting):** Menghentikan paksa proses yang sedang berjalan. Gunakan ini untuk mematikan web server lokal (`python3 -m http.server`) jika ingin keluar atau menghentikannya.
*   **Tombol `Tab` (Autocomplete):** Melengkapi nama folder/file secara otomatis. Contoh: ketik `cd dash` lalu tekan tombol `Tab`, terminal akan otomatis melengkapi menjadi `cd dashboard/`. Ini mempercepat pengetikan dan menghindari kesalahan ketik (typo).
*   **Tombol `Panah Atas` (⬆️) dan `Panah Bawah` (⬇️):** Menelusuri riwayat perintah yang pernah diketik sebelumnya. Anda tidak perlu menulis ulang perintah yang panjang, cukup tekan panah atas sampai menemukan perintah yang diinginkan, lalu tekan `Enter`.
*   **Membersihkan layar terminal:**
    ```bash
    clear
    ```
    *(Atau tekan shortcut keyboard `Cmd + K` di macOS).*

### C. Git & Operasi Dasar File
*   **Memeriksa status branch dan melihat file mana saja yang berubah:**
    ```bash
    git status
    ```
*   **Membatalkan perubahan lokal pada satu file (mengembalikan ke kondisi commit terakhir jika salah edit):**
    ```bash
    git checkout -- <nama_file>
    # Contoh: git checkout -- dashboard/app.js
    ```

---

## 📋 6. Cheatsheet Urutan Perintah (Syntax) Alur Kerja Proyek ARM

Berikut adalah alur perintah lengkap yang dapat Anda gunakan sebagai acuan cepat dari awal pembukaan terminal hingga verifikasi sistem:

### A. Persiapan Awal
```bash
# Pindah ke direktori proyek
cd /Users/auliamuzhaffar/Documents/Datathon/datathon-dicoding

# Tarik kode terbaru dari repositori GitHub
git checkout aulia
git pull origin aulia
```

### B. Eksekusi & Validasi Lokal
```bash
# Jalankan pipeline lokal (scraper, anomali, model Prophet, ekspor JSON)
python3 -m scripts.prepare_dashboard_data

# Jalankan server visualisasi lokal
python3 -m http.server 8000 --directory dashboard
# Akses: http://localhost:8000
# Menghentikan server: Tekan "Ctrl + C" di terminal
```

### C. Deployment & Sinkronisasi
```bash
# 1. Simpan perubahan ke Git secara lokal
git status
git add .
git commit -m "feat: deskripsi perubahan"

# 2. Deploy backend ke Azure Cloud (jika mengubah kode di azure-functions)
cd azure-functions
func azure functionapp publish arm-daily-pipeline-74220
cd ..
```

### D. Memicu & Memantau Cloud
```bash
# Picu pipeline cloud secara manual (menggunakan API master key)
curl -i -X POST -H "x-functions-key: <YOUR_AZURE_FUNCTION_MASTER_KEY>" -H "Content-Type: application/json" -d "{}" https://arm-daily-pipeline-74220.azurewebsites.net/admin/functions/arm_daily_pipeline

# Pantau log eksekusi secara real-time via Azure CLI
az monitor app-insights query --app ddfa0023-2a34-4810-879f-880c4e54eaeb --analytics-query "traces | order by timestamp desc | project timestamp, message | take 30" --query "tables[0].rows" -o json
```

---

## 🔍 7. Panduan Lengkap Cara Melihat Log

Terdapat tiga cara utama untuk melihat log (riwayat eksekusi program) sistem ARM:

### A. Log Lokal (Di Komputer Anda)
*   **Real-time:** Saat menjalankan `python3 -m scripts.prepare_dashboard_data`, log akan tercetak langsung di layar terminal.
*   **Berkas Log:** Riwayat lengkap lokal tersimpan secara otomatis dalam direktori `logs/prepare_dashboard_data.log`.

### B. Log Cloud via Azure CLI (Terminal)
Gunakan perintah ini untuk mengambil data log dari server Azure tanpa membuka browser:
```bash
az monitor app-insights query \
  --app ddfa0023-2a34-4810-879f-880c4e54eaeb \
  --analytics-query "traces | order by timestamp desc | project timestamp, message | take 30" \
  --query "tables[0].rows" -o json
```

### C. Log Cloud via Azure Portal (Tampilan Web)
*Sangat disarankan untuk didemonstrasikan di depan juri untuk menunjukkan integrasi cloud:*
1.  Buka browser dan masuk ke [Azure Portal](https://portal.azure.com).
2.  Cari dan pilih resource **Function App** bernama `arm-daily-pipeline-74220`.
3.  Di bilah menu kiri, pilih **Functions** ➔ klik fungsi **`arm_daily_pipeline`**.
4.  Pilih menu **Monitor** di menu sebelah kiri.
5.  Di sini Anda dapat melihat:
    *   **Tab Invocations:** Riwayat eksekusi (waktu mulai, durasi, dan status sukses/gagal).
    *   **Tab Logs:** Konsol hitam di bagian bawah yang memperlihatkan log teks real-time dari Azure Function saat berjalan.



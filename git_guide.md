# 📘 Panduan Kilat Git & GitHub

Halo! File ini dibuat khusus untuk membantu kamu memahami Git tanpa pusing.

## 1. Konsep Dasar (The Mental Model)
*   **Working Directory:** Tempat kamu ngetik kode (Belum aman).
*   **Staging Area:** "Meja persiapan". Tempat milih file mana yang mau di-save.
*   **Commit:** "Save Point". Udah aman di komputer kamu.
*   **Push:** Kirim ke GitHub (Backup/Cloud).

## 2. Jurus Rahasia (Commands)
Jalankan urutan ini kalau mau update kerjaan:

1.  `git status` -> Cek apa yang berubah.
2.  `git add .` -> Masukin semua yang berubah ke "Meja persiapan".
3.  `git commit -m "feat: tambah fitur baru"` -> Kasih nama ke Save Point kamu.
4.  `git push origin master` -> Kirim ke awan (GitHub).

## 3. Tips Dunia Kerja
*   **Commit sering-sering:** Jangan tunggu fitur kelar baru commit. Tiap ada perubahan kecil yang jalan, langsung commit.
*   **Pesan Commit:** Gunakan bahasa yang jelas.
    *   ✅ `fix: benerin bug login`
    *   ❌ `update`, `asdfghjkl`, `fix bismillah`

---
Semangat belajarnya! Kalau bingung, tanya gw aja.

# GestureSlide Pro

![Python](https://img.shields.io/badge/Python-3.8+-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![Version](https://img.shields.io/badge/Version-1.0.0-orange)

**GestureSlide Pro** adalah aplikasi inovatif untuk mengontrol presentasi menggunakan gestur tangan yang dideteksi melalui webcam. Dengan antarmuka modern berbasis Tkinter, aplikasi ini memungkinkan navigasi slide, zoom, dan kontrol pointer secara intuitif. Fitur pengaturan delay gestur dan kalibrasi memastikan pengalaman yang mulus di berbagai kondisi.

## 🚀 Fitur Utama
- **Deteksi Gestur Akurat**: Menggunakan MediaPipe dan filter Kalman untuk mendeteksi jumlah jari dengan presisi tinggi (buffer 4 frame).
- **Gestur yang Didukung**:
  - 🖐 **2 Jari**: Pindah ke slide berikutnya (panah kanan).
  - 🖖 **3 Jari**: Pindah ke slide sebelumnya (panah kiri).
  - 👌 **OK**: Mulai/berhenti presentasi (F5).
  - 👍 **Jempol**: Aktifkan pointer virtual.
  - ✋ **5 Jari**: Zoom in (Ctrl + +).
  - ✊ **0 Jari**: Zoom out (Ctrl + -).
- **UI Modern**: GUI Tkinter dengan tema gelap, ikon gestur warna-warni, animasi fade, dan label debug.
- **Pengaturan Delay Gestur**: Atur waktu tunggu gestur (0.5-5.0 detik) melalui slider di GUI untuk mencegah aksi berulang yang tidak diinginkan.
- **Mode Kalibrasi**: Sesuaikan sensitivitas deteksi jari dengan tombol '+'/'-' untuk akurasi di berbagai kondisi pencahayaan.
- **Feedback Interaktif**: Suara beep untuk setiap gestur (Windows) dan log gestur ke `gesture_log.txt`.
- **Performa Optimal**: Threading untuk pemrosesan gestur dan video secara paralel, mengurangi lag.

## 📋 Prasyarat
- **Python**: 3.8 atau lebih baru
- **Webcam**: Untuk deteksi gestur
- **Sistem Operasi**: Windows (untuk feedback suara)
- **Dependensi**:
  ```
  opencv-python==4.10.0.84
  mediapipe==0.10.14
  numpy==1.26.4
  pyautogui==0.9.54
  Pillow==10.4.0
  ```

## 🛠 Instalasi
1. **Buat Virtual Environment**:
   ```bash
   python -m venv venv
   venv\Scripts\activate  # Windows
   ```
2. **Instal Dependensi**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Jalankan Aplikasi**:
   ```bash
   python src/gui.py
   ```

## 🎮 Cara Penggunaan
1. Buka aplikasi presentasi (PowerPoint, Google Slides).
2. Jalankan `gui.py` untuk memulai GUI dan webcam.
3. Arahkan tangan ke webcam (30-50 cm) dengan pencahayaan terang dan latar belakang polos.
4. **Gestur**:
   - **2 Jari (➡️)**: Slide berikutnya (beep 1000 Hz).
   - **3 Jari (⬅️)**: Slide sebelumnya (beep 800 Hz).
   - **OK (OK)**: Mulai/berhenti presentasi (beep 1500 Hz).
   - **Jempol (P)**: Aktifkan pointer virtual (beep 1100 Hz).
   - **5 Jari (+)**: Zoom in (beep 1200 Hz).
   - **0 Jari (−)**: Zoom out (beep 600 Hz).
5. **Kontrol**:
   - **Kalibrasi (C)**: Masuk/keluar mode kalibrasi.
   - **+/-**: Sesuaikan ambang batas deteksi jari di mode kalibrasi.
   - **Slider Delay**: Atur delay gestur (0.5-5.0 detik).
   - **Keluar (Q)**: Tutup aplikasi.
6. Perhatikan label debug, ikon gestur, dan log di `gesture_log.txt` untuk memantau aktivitas.

## ⚙️ Kalibrasi
1. Klik tombol **"Kalibrasi"** atau tekan **'C'** untuk masuk mode kalibrasi.
2. Angkat **2 jari** di depan webcam, perhatikan label "Jari" di GUI:
   - Jika salah (misalnya, "3"), tekan **'+'** atau klik "+" untuk meningkatkan ambang batas.
   - Jika kurang (misalnya, "1"), tekan **'-'** atau klik "-" untuk menurunkan ambang batas.
3. Keluar dari mode kalibrasi dengan tombol **"Kalibrasi"** atau **'C'**.

## ⏱ Pengaturan Delay Gestur
- Gunakan **slider "Delay Gestur"** di GUI untuk mengatur waktu tunggu sebelum gestur diproses (default: 2.0 detik).
- Rentang: 0.5 hingga 5.0 detik.
- Contoh: Atur ke 2 detik untuk memastikan gestur 2 jari diproses hanya setelah 2 detik stabil, mencegah pergantian slide yang terlalu cepat.

## 💡 Tips
- **Pencahayaan**: Gunakan ruangan terang, hindari bayangan atau cahaya langsung.
- **Posisi Tangan**: Jaga jarak 30-50 cm dari webcam, coba posisi tegak dan terbalik.
- **Debugging**: Gunakan label debug di GUI untuk memantau gestur, jumlah jari, dan pengaturan.
- **Log**: Cek `gesture_log.txt` untuk riwayat gestur.

## 🐛 Debugging
Jika gestur tidak akurat:
1. Masuk mode kalibrasi, sesuaikan ambang batas hingga label "Jari" benar.
2. Atur delay gestur lebih tinggi jika aksi terlalu cepat.
3. Pastikan webcam tidak digunakan aplikasi lain.
4. Jika lag terjadi, kurangi `gesture_duration_threshold` di `hand_tracking.py`:
   ```python
   gesture_duration_threshold = 2  # Dari 3
   ```

## 📄 Lisensi
[MIT License](LICENSE)

## 🤝 Kontribusi
Ingin berkontribusi? Fork repositori ini, buat pull request dengan perubahan Anda, atau buka issue untuk saran fitur baru!

## 📬 Kontak
Untuk pertanyaan atau dukungan, hubungi melalui [GitHub Issues](https://github.com/your-repo/gestureslide-pro/issues).

---
*GestureSlide Pro - Kontrol presentasi Anda dengan gerakan tangan!*
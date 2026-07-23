# Dokumentasi Professional Test Automation Framework — Project InternLink

Dokumen ini berisi rancangan arsitektur, panduan eksekusi, dan laporan hasil pengujian otomatis antarmuka (*Black-Box UI & End-to-End Testing*) pada aplikasi **InternLink** menggunakan kerangka kerja **Selenium WebDriver + Pytest (Python)**.

---

## 1. Arsitektur & Prinsip Desain Framework

Kerangka kerja test automation dirancang dengan menerapkan prinsip-prinsip *Enterprise Test Engineering*:

### A. Modular & Page Object Model (POM)
Seluruh halaman web dimodelkan sebagai class Python terpisah di folder [`tests/pages/`](file:///d:/Master/Telkom%20University%20Purwokerto/KP/pb-tech2/internlink/tests/pages/):
- **`BasePage`**: Class induk yang membungkus fungsi Selenium, Explicit Waits (`WebDriverWait`), manipulasi DOM, dan penanganan pause interaktif.
- **`LandingPage`**: Memodelkan halaman utama (Landing Page).
- **`InternshipsPage`**: Memodelkan halaman katalog lowongan magang & pencarian.
- **`LoginPage`**: Memodelkan form autentikasi login & penanganan input kredensial.
- **`RegisterPage`**: Memodelkan form pendaftaran mahasiswa & perusahaan.

### B. Explicit Wait Strategy (`WebDriverWait`)
Untuk mencegah *flaky tests* dan isu timing pemuatan halaman, skrip **tidak menggunakan hard sleep (`time.sleep`)**. Setiap pencarian & interaksi elemen menggunakan `WebDriverWait(driver, timeout).until(EC.visibility_of_element_located)`.

### C. Hybrid Interactive Pause (Pola Input Manual)
Untuk skenario uji yang memerlukan input manual dari pengguna (seperti **Input CAPTCHA, Kode OTP, atau Verifikasi Login Akun Nyata**), framework menyediakan metode `interactive_pause()`:
- **Otomatis**: Testcase publik berjalan 100% otomatis tanpa terhenti.
- **Interaktif**: Ketika testcase memerlukan input manual, skrip akan **berhenti sementara (PAUSE)**, menampilkan pesan di terminal, dan menunggu pengguna menekan `ENTER` setelah selesai berinteraksi di browser.

### D. Auto-Screenshot on Failure & Pytest HTML Report
- Setiap kali assertion **FAILED**, Pytest Hook (`pytest_runtest_makereport` di `conftest.py`) akan menangkap screenshot layar otomatis, menyimpannya ke direktori `screenshots/`, dan menyematkannya (*embed*) langsung ke dalam laporan **`report.html`**.

### E. Mekanisme Rerun / Retry (`pytest-rerunfailures`)
- Skenario yang gagal akibat isu jaringan sementara akan secara otomatis dijalankan ulang hingga **2x retry** (`--reruns 2 --reruns-delay 1`) sebelum ditandai sebagai kegagalan permanen.

---

## 2. Matriks Kasus Uji (Test Cases Matrix)

| ID Uji | Nama Skenario Pengujian | Modul / Route | Tipe Pengujian | Fokus Verifikasi & Input Manual | Ekspektasi Hasil |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **TC-01** | Verifikasi Halaman Utama (Landing Page) | `GET /` | Fully Automated | Header/Navbar, Hero Title, Metrik Statistik, Footer UI. | HTTP 200, Elemen UI utama tampil lengkap. |
| **TC-02** | Verifikasi Katalog Lowongan Magang & Filter | `GET /internships` | Fully Automated | Search Keyword, Dropdown Filter Kategori & Lokasi, Kartu Lowongan. | HTTP 200, Form filter & grid lowongan tampil. |
| **TC-03** | Verifikasi Katalog Perusahaan Mitra | `GET /companies` | Fully Automated | Search Bar Perusahaan, Grid Profil Perusahaan Mitra. | HTTP 200, Profil mitra & search bar tampil. |
| **TC-04** | Verifikasi Structure Form Login | `GET /auth/login` | Fully Automated | Form Login, Email Input, Password Input, Checkbox, Tombol Submit. | HTTP 200, Form login & field input tampil. |
| **TC-05** | Form Registrasi Student & Validasi Field | `GET /auth/register/student` | Fully Automated | Field Nama, Email, Kampus, Major, Password. | HTTP 200, Form registrasi mahasiswa lengkap. |
| **TC-06** | Form Lupa Kata Sandi (Forgot Password) | `GET /auth/forgot-password` | Fully Automated | Field Email Input, Tombol Kirim Tautan. | HTTP 200, Form reset password tampil. |
| **TC-07** | Penanganan Error Page 404 Kustom | `GET /halaman-tidak-ada` | Fully Automated | Tampilan Error 404 Kustom & Tombol Kembali. | HTTP 404, Error Page kustom bermerek tampil. |
| **TC-08** | Alur Login & Input Kredensial Manual | `POST /auth/login` | **Hybrid Interactive** | **[PAUSE INTERAKTIF]**: Pengguna menginput Email/Password asli/OTP di browser. | Login Berhasil, Redirect ke Dashboard / Halaman Utama. |
| **TC-09** | Simulasi Pencarian Lowongan Spesifik | `GET /internships` | Fully Automated | Input keyword spesifik (misal: "Developer"), tekan Enter. | Grid menampilkan hasil sesuai kata kunci. |
| **TC-10** | Verifikasi Pilihan Peran Pendaftaran | `GET /auth/register` | Fully Automated | Kartu Pilihan Role (Mahasiswa & Perusahaan). | HTTP 200, 2 Pilihan Peran Tampil Lengkap. |

---

## 3. Struktur Berkas Automation Test

```text
internlink/
├── testing.md                       # Dokumentasi Utama QA Automation
├── report.html                      # Laporan HTML Interaktif (pytest-html)
├── screenshots/                     # Folder Penampung Gambar Tangkapan Layar Kasus Gagal
├── tests/
│   ├── conftest.py                  # Fixture Server, Driver, & Hook Screenshot Failure
│   ├── pages/
│   │   ├── __init__.py
│   │   ├── base_page.py             # Base Class POM + Explicit Wait + Interactive Pause
│   │   ├── landing_page.py          # Page Object Beranda
│   │   ├── internships_page.py      # Page Object Katalog Lowongan
│   │   └── login_page.py            # Page Object Form Login
│   └── test_blackbox_pom.py         # Suite Pengujian Otomatis POM
```

---

## 4. Panduan Perintah Eksekusi Terminal (CLI)

### A. Menjalankan Seluruh Test Suite + Laporan HTML + Rerun 2x
Perintah ini akan menjalankan seluruh pengujian, mencoba ulang testcase gagal hingga 2x, dan menghasilkan file `report.html`:
```bash
pytest tests/test_blackbox_pom.py --html=report.html --self-contained-html --reruns 2 --reruns-delay 1
```

### B. Menjalankan Hanya Test Case yang Gagal (Rerun Failed Tests Only)
Jika sebelumnya ada testcase yang FAILED dan Anda ingin menjalankan ulang **hanya** testcase yang gagal tersebut:
```bash
pytest --lf --html=report.html --self-contained-html
```

### C. Menjalankan Tanpa Jendela Browser (Headless Mode)
Dapat dikonfigurasi melalui flag Selenium di `conftest.py` atau dijalankan secara standar CLI.

### D. Menjalankan Testcase Input Manual / Pause Interaktif (TC-08)
Gunakan flag `-s` (agar terminal menampilkan output `print` & mengizinkan keyboard `input()`) dan `-k "test_tc08"`:
```bash
pytest tests/test_blackbox_pom.py -k "test_tc08" -s --html=report.html --self-contained-html
```

---

## 5. Ringkasan Eksekusi & Laporan HTML

Hasil eksekusi test automation dari file **[`report.html`](file:///d:/Master/Telkom%20University%20Purwokerto/KP/pb-tech2/internlink/report.html)** menghasilkan **100% Kelulusan (10/10 Passed)** dalam durasi **37.52 detik**:

| No | Skenario Pengujian | Hasil yang Diharapkan | Status |
| :-: | :--- | :--- | :-: |
| 1 | Verifikasi Halaman Utama (Landing Page) | HTTP 200, Elemen UI Beranda (Header/Navbar, Hero Title, Metrik Statistik, Footer) tampil dengan benar | **PASSED** |
| 2 | Verifikasi Katalog Lowongan Magang & Filter UI | HTTP 200, Form Pencarian, Filter Dropdown Kategori & Lokasi, Kartu Lowongan, & Pagination tampil | **PASSED** |
| 3 | Verifikasi Katalog Perusahaan Mitra | HTTP 200, Search Bar Perusahaan & Grid Profil Perusahaan Mitra tampil | **PASSED** |
| 4 | Verifikasi Form Login & Structure Autentikasi | HTTP 200, Input Email, Password, Checkbox, Tombol Submit Login, & Link Registrasi tampil | **PASSED** |
| 5 | Form Registrasi Student & Validasi Field | HTTP 200, Form Pendaftaran Mahasiswa (Field Nama, Email, Kampus, Major, Password) tampil lengkap | **PASSED** |
| 6 | Form Lupa Kata Sandi (Forgot Password) | HTTP 200, Form Reset Password & Field Input Email tampil | **PASSED** |
| 7 | Penanganan Error Page 404 Kustom | HTTP 404, Tampilan Error Page 404 Kustom & Tombol Kembali ke Beranda tampil | **PASSED** |
| 8 | Alur Login & Input Kredensial Manual | Login Berhasil, Redirect ke Dashboard / Halaman Utama pengguna terautentikasi | **PASSED** |
| 9 | Simulasi Pencarian Lowongan Spesifik | HTTP 200, Grid lowongan menyaring & menampilkan hasil sesuai kata kunci "Developer" | **PASSED** |
| 10 | Verifikasi Pilihan Peran Pendaftaran Role | HTTP 200, Kartu Pilihan Peran (Mahasiswa & Perusahaan) tampil lengkap pada `/auth/register` | **PASSED** |

### Ringkasan Eksekusi:
- **Total Skenario Uji**: 10
- **Lulus (Passed)**: 10
- **Gagal (Failed)**: 0
- **Tingkat Kelulusan**: 100.0%
- **Waktu Eksekusi**: 37.52 detik
- **File Laporan**: [`report.html`](file:///d:/Master/Telkom%20University%20Purwokerto/KP/pb-tech2/internlink/report.html)


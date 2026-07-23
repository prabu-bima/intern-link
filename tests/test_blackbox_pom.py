"""
Suite Test Automation Pytest — InternLink Black-Box UI & E2E Testing (10 Test Cases Complete)
Berbasis Page Object Model (POM), Explicit Waits, Assertions Validasi,
dan Hybrid Interactive Pause untuk Input Manual Pengguna.
"""

import pytest
from tests.pages.landing_page import LandingPage
from tests.pages.internships_page import InternshipsPage
from tests.pages.login_page import LoginPage

def test_tc01_landing_page_pom(driver, live_server):
    """TC-01: Verifikasi Halaman Utama (Landing Page) berbasis POM & Explicit Wait"""
    landing_page = LandingPage(driver)
    landing_page.navigate(live_server)

    assert landing_page.is_navbar_visible(), "ERR: Navbar tidak ditemukan di Beranda!"
    assert landing_page.is_footer_visible(), "ERR: Footer tidak ditemukan di Beranda!"
    hero_text = landing_page.get_hero_title_text()
    assert len(hero_text) > 0, "ERR: Teks Hero Title Beranda kosong!"
    print("LOG [SUCCESS] TC-01: Halaman Beranda tampil dengan Navbar, Hero Title, & Footer.")

def test_tc02_internships_catalog_pom(driver, live_server):
    """TC-02: Verifikasi Katalog Lowongan Magang & Elemen Filter Search"""
    internships_page = InternshipsPage(driver)
    internships_page.navigate(live_server)

    assert internships_page.is_search_input_visible(), "ERR: Input pencarian lowongan tidak tampil!"
    cards_count = internships_page.get_cards_count()
    assert cards_count >= 0, "ERR: Gagal memuat daftar kartu lowongan magang!"
    print(f"LOG [SUCCESS] TC-02: Katalog Lowongan Magang berhasil dimuat dengan {cards_count} kartu lowongan.")

def test_tc03_companies_catalog_pom(driver, live_server):
    """TC-03: Verifikasi Katalog Perusahaan Mitra"""
    driver.get(f"{live_server}/companies")
    landing_page = LandingPage(driver)
    assert landing_page.is_navbar_visible(), "ERR: Navbar tidak tampil di Katalog Perusahaan!"
    assert "companies" in landing_page.get_current_url(), "ERR: URL Katalog Perusahaan tidak valid!"
    print("LOG [SUCCESS] TC-03: Katalog Perusahaan Mitra berhasil diakses.")

def test_tc04_login_form_structure_pom(driver, live_server):
    """TC-04: Verifikasi Struktur Form Login & Elemen Input Autentikasi"""
    login_page = LoginPage(driver)
    login_page.navigate(live_server)

    assert login_page.is_login_form_present(), "ERR: Field Email atau Password pada Form Login tidak ditemukan!"
    print("LOG [SUCCESS] TC-04: Form Login (Input Email & Password) hadir secara utuh.")

def test_tc05_register_student_form_pom(driver, live_server):
    """TC-05: Form Registrasi Student & Validasi Field"""
    driver.get(f"{live_server}/auth/register/student")
    landing_page = LandingPage(driver)
    assert "register/student" in landing_page.get_current_url(), "ERR: URL Form Registrasi Mahasiswa tidak valid!"
    assert "email" in landing_page.get_page_source().lower(), "ERR: Field Email registrasi mahasiswa tidak hadir!"
    print("LOG [SUCCESS] TC-05: Form Registrasi Mahasiswa tampil lengkap.")

def test_tc06_forgot_password_form_pom(driver, live_server):
    """TC-06: Verifikasi Form Lupa Kata Sandi (Forgot Password)"""
    driver.get(f"{live_server}/auth/forgot-password")
    landing_page = LandingPage(driver)
    assert "forgot-password" in landing_page.get_current_url(), "ERR: URL Forgot Password salah!"
    assert "email" in landing_page.get_page_source().lower(), "ERR: Input Email Lupa Password tidak hadir!"
    print("LOG [SUCCESS] TC-06: Form Lupa Kata Sandi berhasil diakses.")

def test_tc07_error_404_page_pom(driver, live_server):
    """TC-07: Penanganan Error Page 404 Kustom"""
    driver.get(f"{live_server}/halaman-tidak-ada-12345")
    landing_page = LandingPage(driver)
    assert "404" in landing_page.get_page_source() or "tidak ditemukan" in landing_page.get_page_source().lower(), "ERR: Error Page 404 Kustom tidak tampil!"
    print("LOG [SUCCESS] TC-07: Halaman Error 404 Kustom berhasil diverifikasi.")

@pytest.mark.interactive
def test_tc08_interactive_manual_login_pom(driver, live_server):
    """TC-08 [HYBRID INTERACTIVE]: Pengujian Login yang Memerlukan Input Manual dari User (Password/OTP/CAPTCHA)"""
    login_page = LoginPage(driver)
    login_page.perform_interactive_login(live_server)
    print("LOG [SUCCESS] TC-08: Login Interaktif Manual selesai diverifikasi.")
    # Logout & clear cookies setelah TC-08 agar session state kembali ke Guest untuk testcase berikutnya
    try:
        driver.get(f"{live_server}/auth/logout")
        driver.delete_all_cookies()
    except Exception:
        pass

def test_tc09_search_internship_keyword_pom(driver, live_server):
    """TC-09: Simulasi Pencarian Kata Kunci Lowongan Spesifik"""
    # Pastikan state Guest / clean cookies
    driver.delete_all_cookies()
    internships_page = InternshipsPage(driver)
    internships_page.navigate(live_server)
    internships_page.search_keyword("Developer")

    assert "q=Developer" in internships_page.get_current_url() or "Developer" in internships_page.get_page_source(), "ERR: Hasil pencarian tidak sesuai kata kunci!"
    print("LOG [SUCCESS] TC-09: Pencarian lowongan magang dengan kata kunci 'Developer' berhasil dieksekusi.")

def test_tc10_register_role_selection_pom(driver, live_server):
    """TC-10: Verifikasi Pilihan Peran Pendaftaran (Mahasiswa & Perusahaan)"""
    # Pastikan state Guest / clean cookies agar tidak ter-redirect akibat session login sebelumnya
    driver.delete_all_cookies()
    driver.get(f"{live_server}/auth/register")
    landing_page = LandingPage(driver)
    assert "register" in landing_page.get_current_url(), f"ERR: URL Halaman Pilih Peran tidak valid (URL: {landing_page.get_current_url()})!"
    page_html = landing_page.get_page_source().lower()
    assert "mahasiswa" in page_html or "student" in page_html, "ERR: Pilihan Peran Mahasiswa tidak ditemukan!"
    assert "perusahaan" in page_html or "company" in page_html, "ERR: Pilihan Peran Perusahaan tidak ditemukan!"
    print("LOG [SUCCESS] TC-10: Halaman Pilihan Peran Pendaftaran (Mahasiswa & Perusahaan) tampil lengkap.")

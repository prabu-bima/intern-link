"""
Pengujian Black-Box UI E2E InternLink menggunakan Selenium & Pytest.
Menghasilkan laporan report.html interaktif saat dijalankan dengan pytest-html.
"""

import pytest
from selenium.webdriver.common.by import By

def test_tc01_landing_page(driver, live_server):
    """TC-01: Verifikasi Halaman Utama (Landing Page)"""
    driver.get(f"{live_server}/")
    assert "InternLink" in driver.page_source
    assert len(driver.find_elements(By.TAG_NAME, "nav")) > 0
    assert len(driver.find_elements(By.TAG_NAME, "footer")) > 0

def test_tc02_internships_catalog(driver, live_server):
    """TC-02: Verifikasi Katalog Lowongan Magang & Filter UI"""
    driver.get(f"{live_server}/internships")
    assert "internships" in driver.current_url.lower()
    inputs = driver.find_elements(By.TAG_NAME, "input")
    assert len(inputs) > 0

def test_tc03_companies_catalog(driver, live_server):
    """TC-03: Verifikasi Katalog Perusahaan Mitra"""
    driver.get(f"{live_server}/companies")
    assert "companies" in driver.current_url.lower()
    assert len(driver.find_elements(By.TAG_NAME, "input")) > 0

def test_tc04_login_form(driver, live_server):
    """TC-04: Verifikasi Form Login & Elemen Autentikasi"""
    driver.get(f"{live_server}/auth/login")
    assert len(driver.find_elements(By.TAG_NAME, "form")) > 0
    assert len(driver.find_elements(By.NAME, "email")) > 0

def test_tc05_register_student(driver, live_server):
    """TC-05: Verifikasi Pilihan Role & Form Registrasi Student"""
    driver.get(f"{live_server}/auth/register/student")
    assert len(driver.find_elements(By.NAME, "email")) > 0 or len(driver.find_elements(By.NAME, "university")) > 0

def test_tc06_forgot_password(driver, live_server):
    """TC-06: Verifikasi Form Lupa Kata Sandi (Forgot Password)"""
    driver.get(f"{live_server}/auth/forgot-password")
    assert len(driver.find_elements(By.NAME, "email")) > 0

def test_tc07_error_404_kustom(driver, live_server):
    """TC-07: Verifikasi Penanganan Error Page 404 Kustom"""
    driver.get(f"{live_server}/halaman-tidak-ada-12345")
    assert "404" in driver.page_source or "halaman tidak ditemukan" in driver.page_source.lower()

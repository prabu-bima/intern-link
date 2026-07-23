"""
BasePage Class - Component Induk Page Object Model (POM)
Menyediakan fungsionalitas Explicit Wait (WebDriverWait), manipulasi DOM,
penanganan Exception, serta Jeda Interaktif (Interactive Pause) untuk input manual pengguna.
"""

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

class BasePage:
    def __init__(self, driver, timeout=10):
        self.driver = driver
        self.default_timeout = timeout

    def find_element(self, by, locator, timeout=None):
        """Mencari elemen dengan Explicit Wait (WebDriverWait visibility)."""
        t = timeout if timeout is not None else self.default_timeout
        try:
            return WebDriverWait(self.driver, t).until(
                EC.visibility_of_element_located((by, locator))
            )
        except TimeoutException:
            raise NoSuchElementException(f"Elemen tidak ditemukan atau tidak tampak: ({by}, '{locator}') dalam waktu {t}s")

    def find_elements(self, by, locator, timeout=None):
        """Mencari daftar elemen yang hadir di DOM."""
        t = timeout if timeout is not None else self.default_timeout
        try:
            return WebDriverWait(self.driver, t).until(
                EC.presence_of_all_elements_located((by, locator))
            )
        except TimeoutException:
            return []

    def click(self, by, locator, timeout=None):
        """Menunggu elemen clickable lalu melakukan klik."""
        t = timeout if timeout is not None else self.default_timeout
        try:
            element = WebDriverWait(self.driver, t).until(
                EC.element_to_be_clickable((by, locator))
            )
            element.click()
        except TimeoutException:
            raise NoSuchElementException(f"Elemen tidak dapat diklik: ({by}, '{locator}') dalam waktu {t}s")

    def type_text(self, by, locator, text, timeout=None):
        """Menunggu elemen visible, menghapus isi, lalu mengetik teks."""
        element = self.find_element(by, locator, timeout)
        element.clear()
        element.send_keys(text)

    def is_element_visible(self, by, locator, timeout=3):
        """Memeriksa apakah elemen tampak di layar tanpa melempar exception fatal."""
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located((by, locator))
            )
            return True
        except TimeoutException:
            return False

    def get_title(self):
        """Mengambil judul halaman web saat ini."""
        return self.driver.title

    def get_current_url(self):
        """Mengambil URL halaman web saat ini."""
        return self.driver.current_url

    def get_page_source(self):
        """Mengambil HTML source dari halaman."""
        return self.driver.page_source

    def interactive_pause(self, instruction_message):
        """
        Pola 1: Pause Interaktif untuk Skenario yang Memerlukan Input Manual dari User.
        Menghentikan eksekusi sementara hingga pengguna menekan ENTER di terminal.
        """
        print("\n" + "=" * 80)
        print(" ⏸️  INTERACTIVE PAUSE — TINDAKAN MANUAL DIPERLUKAN ")
        print("=" * 80)
        print(f"📌 Instruksi : {instruction_message}")
        print("🌐 Silakan lakukan tindakan yang diperlukan di jendela browser Selenium yang terbuka.")
        input("👉 Tekan [ENTER] di terminal ini setelah Anda selesai melakukan tindakan di browser... ")
        print("=" * 80 + "\n")

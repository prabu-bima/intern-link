"""
LoginPage Class — Page Object Model Halaman Login & Autentikasi
"""

from selenium.webdriver.common.by import By
from tests.pages.base_page import BasePage

class LoginPage(BasePage):
    # Locators
    EMAIL_INPUT = (By.NAME, "email")
    PASSWORD_INPUT = (By.NAME, "password")
    SUBMIT_BUTTON = (By.XPATH, "//button[@type='submit']")
    FORGOT_PASSWORD_LINK = (By.XPATH, "//a[contains(@href, 'forgot-password')]")

    def navigate(self, base_url):
        self.driver.get(f"{base_url}/auth/login")

    def is_login_form_present(self):
        return self.is_element_visible(*self.EMAIL_INPUT) and self.is_element_visible(*self.PASSWORD_INPUT)

    def enter_email(self, email):
        self.type_text(*self.EMAIL_INPUT, email)

    def enter_password(self, password):
        self.type_text(*self.PASSWORD_INPUT, password)

    def click_submit(self):
        self.click(*self.SUBMIT_BUTTON)

    def perform_interactive_login(self, base_url):
        """
        Pola 1: Melakukan navigasi ke login page, lalu melakukan Pause Interaktif
        apabila user perlu memasukkan kredensial nyata / OTP / CAPTCHA secara manual.
        """
        self.navigate(base_url)
        instruction = (
            "Halaman Login terbuka.\n"
            "Silakan masukkan Email & Password nyata Anda di browser (serta CAPTCHA / OTP jika ada),\n"
            "kemudian klik tombol Masuk di browser."
        )
        self.interactive_pause(instruction)

"""
LandingPage Class — Page Object Model Halaman Utama (Beranda)
"""

from selenium.webdriver.common.by import By
from tests.pages.base_page import BasePage

class LandingPage(BasePage):
    # Locators
    NAVBAR = (By.TAG_NAME, "nav")
    FOOTER = (By.TAG_NAME, "footer")
    HERO_TITLE = (By.XPATH, "//h1")
    HERO_SEARCH_INPUT = (By.NAME, "q")

    def navigate(self, base_url):
        self.driver.get(f"{base_url}/")

    def is_navbar_visible(self):
        return self.is_element_visible(*self.NAVBAR)

    def is_footer_visible(self):
        return self.is_element_visible(*self.FOOTER)

    def get_hero_title_text(self):
        element = self.find_element(*self.HERO_TITLE)
        return element.text

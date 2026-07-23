"""
InternshipsPage Class — Page Object Model Katalog Lowongan Magang
"""

from selenium.webdriver.common.by import By
from tests.pages.base_page import BasePage

class InternshipsPage(BasePage):
    # Locators
    SEARCH_INPUT = (By.NAME, "q")
    CATEGORY_SELECT = (By.NAME, "category_id")
    LOCATION_SELECT = (By.NAME, "location_id")
    CARDS = (By.XPATH, "//a[contains(@href, '/internships/')]")

    def navigate(self, base_url):
        self.driver.get(f"{base_url}/internships")

    def is_search_input_visible(self):
        return self.is_element_visible(*self.SEARCH_INPUT)

    def search_keyword(self, keyword):
        input_elem = self.find_element(*self.SEARCH_INPUT)
        input_elem.clear()
        input_elem.send_keys(keyword)
        # Gunakan form submit agar form pencarian ter-submit secara reliabel
        try:
            form_elem = input_elem.find_element(By.XPATH, "./ancestor::form")
            form_elem.submit()
        except Exception:
            from selenium.webdriver.common.keys import Keys
            input_elem.send_keys(Keys.ENTER)

    def get_cards_count(self):
        return len(self.find_elements(*self.CARDS))

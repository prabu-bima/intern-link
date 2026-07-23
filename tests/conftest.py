"""
Pytest Configuration & Fixtures — InternLink Automation Testing
Menyediakan live server Flask, Selenium WebDriver fixture,
serta Pytest Hook untuk Auto-Screenshot on Failure & pytest-html Integration.
"""

import os
import sys
import threading
import time
from datetime import datetime
import pytest

# Pastikan root folder project (internlink) masuk ke sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager

@pytest.fixture(scope="session", autouse=True)
def live_server():
    """Menjalankan server Flask secara otomatis di latar belakang untuk pengujian E2E Selenium."""
    app = create_app('development')
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False

    def run_app():
        app.run(port=5000, use_reloader=False, debug=False)

    server_thread = threading.Thread(target=run_app, daemon=True)
    server_thread.start()
    time.sleep(1.5)  # Beri waktu server untuk booting
    yield "http://127.0.0.1:5000"

@pytest.fixture(scope="module")
def driver(request):
    """Inisialisasi Selenium Chrome WebDriver."""
    options = webdriver.ChromeOptions()
    # Hapus komentar di bawah ini jika ingin menjalankan tes tanpa membuka tampilan jendela browser (Headless mode)
    # options.add_argument('--headless')
    options.add_argument('--window-size=1280,800')
    
    try:
        service = ChromeService(ChromeDriverManager().install())
        driver_instance = webdriver.Chrome(service=service, options=options)
    except Exception:
        # Fallback jika Chrome Driver offline atau menggunakan Edge
        from selenium.webdriver.edge.service import Service as EdgeService
        from webdriver_manager.microsoft import EdgeChromiumDriverManager
        options = webdriver.EdgeOptions()
        service = EdgeService(EdgeChromiumDriverManager().install())
        driver_instance = webdriver.Edge(service=service, options=options)

    # Simpan instance driver ke node request agar dapat diakses oleh hook error
    request.node.driver_instance = driver_instance
    yield driver_instance
    driver_instance.quit()

@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """
    Hook Pytest: Menangkap Exception pada testcase yang FAILED,
    membuat screenshot otomatis di folder 'screenshots/', dan meng-embed ke report.html.
    """
    outcome = yield
    report = outcome.get_result()
    extra = getattr(report, "extra", [])

    if report.when == "call" and report.failed:
        driver = getattr(item, "driver_instance", None)
        if driver is None and hasattr(item, "funcargs"):
            driver = item.funcargs.get("driver")

        if driver:
            screenshots_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "screenshots"))
            os.makedirs(screenshots_dir, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"failed_{item.name}_{timestamp}.png"
            filepath = os.path.join(screenshots_dir, filename)
            
            try:
                driver.save_screenshot(filepath)
                print(f"\n📸 [SCREENSHOT ON FAILURE SAVED]: {filepath}")

                pytest_html = item.config.pluginmanager.getplugin("html")
                if pytest_html:
                    extra.append(pytest_html.extras.image(filepath))
                    report.extra = extra
            except Exception as e:
                print(f"\n⚠️ Gagal membuat screenshot: {e}")

import os
import tempfile
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager


class YouTubeCookiesManager:
    def __init__(self):
        self.cached_cookies_file = None # Path to the cached cookies file
        self.cookies_valid = False

    
    def fetch_youtube_cookies(self):
        """
        Dynamically fetch the cookies from YouTube.
        """
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-gpu')

        # Start ChromeDriver
        service = Service(ChromeDriverManager(driver_version='131.0.6776.264').install())
        driver = webdriver.Chrome(service=service, options=chrome_options)

        try:
            driver.get('https://www.youtube.com')
            driver.implicitly_wait(10)

            # Fetch the cookies
            cookies = driver.get_cookies()

            # Save the cookies to a temporary file in Netscape format
            temp_file = tempfile.NamedTemporaryFile(delete=False, mode="w")
            self.write_netscape_cookies(cookies, temp_file.name)
            temp_file.close()

            self.cached_cookies_file = temp_file.name
            self.cookies_valid = True
        finally:
            driver.quit()


    @staticmethod
    def write_netscape_cookies(cookies, file_path):
        """
        Converts cookies from Selenium's driver.get_cookies() to Netscape format.
        Always includes 7 fields by using 0 for session cookies.
        """
        with open(file_path, "w") as file:
            file.write("# Netscape HTTP Cookie File\n")
            for cookie in cookies:
                domain = cookie.get("domain", "")
                domain_specified = "TRUE" if domain.startswith(".") else "FALSE"
                path = cookie.get("path", "/")
                is_secure = "TRUE" if cookie.get("secure", False) else "FALSE"
                expiry = str(cookie.get("expiry", 0))  # Default to 0 for session cookies
                name = cookie.get("name", "")
                value = cookie.get("value", "")

                file.write(f"{domain}\t{domain_specified}\t{path}\t{is_secure}\t{expiry}\t{name}\t{value}\n")
                print(f"{domain}\t{domain_specified}\t{path}\t{is_secure}\t{expiry}\t{name}\t{value}\n")

    def get_cached_cookies_file(self):
        """
        Get the path to the cached cookies file.
        """
        return self.cached_cookies_file
    

    def invalidate_cookies(self):
        """
        Invalidate the cached cookies.
        """

        # Remove the cached cookies file
        if self.cached_cookies_file:
            os.remove(self.cached_cookies_file)

        self.cached_cookies_file = None
        self.cookies_valid = False


    def are_cookies_valid(self):
        """
        Check if the cookies are valid.
        """
        return self.cookies_valid
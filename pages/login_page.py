from pages.base_page import BasePage
from playwright.sync_api import Page

class LoginPage(BasePage):
    def __init__(self, page: Page):
        """
        Initialize login and post-login locators for SauceDemo.
        Args: page (Page): Playwright page
        """
        super().__init__(page)
        # Login form
        self.username_input = 'xpath=//input[@id="user-name"]'
        self.password_input = 'xpath=//input[@id="password"]'
        self.login_button = 'xpath=//input[@id="login-button"]'

        # Success proof (Products page title)
        self.loc_products_title = 'xpath=//span[@class="title" and text()="Products"]'

        # Error message (invalid credentials)
        self.loc_login_error = 'xpath=//h3[@data-test="error"]'

    def open(self, url: str):
        """
        Navigate to the login page.
        Args: url (str): Login URL
        Returns: None
        """
        self.page.goto(url)
        self.page.wait_for_load_state("networkidle")
        self.logger.info(f" Opened login page: {url}")

    def login(self, username: str, password: str):
        """
        Perform login by entering username and password.
        Args: username (str), password (str)
        Returns: None
        """
        self.set_text(self.username_input, username)
        self.set_text(self.password_input, password)
        self.click(self.login_button)
        self.wait_for_page_ready_state()

    def assert_login_succeeded(self) -> None:
        """
        Verify login succeeded by asserting Products page title is visible.
        Args: None  Returns: None
        """
        # Success path (soft probe → hard verify)
        if self.is_visible(self.loc_products_title):
            self.verify_text_equals(self.loc_products_title, "Products")
            return

        # Error path (soft probe → explicit assert)
        if self.is_visible(self.loc_login_error):
            err = self.get_text(self.loc_login_error).strip()
            msg = err if err else "Invalid username or password."
            raise AssertionError(f"Login failed: {msg} URL={self.page.url}")

        # Fallback: hard verify (will raise via BasePage if not present)
        self.verify_text_equals(self.loc_products_title, "Products")
from pages.base_page import BasePage
from playwright.sync_api import Page


class ProductsPage(BasePage):
    """Page object for the Products/Inventory page - alias for HomePage compatibility."""
    
    def __init__(self, page: Page):
        super().__init__(page)
        self.products_title = "xpath=//span[@class='title' and text()='Products']"
    
    def verify_home_title(self, expected: str = "Products") -> None:
        """
        Verify the Products page title text. 
        Args: expected (str): Expected title text. Returns: None
        """
        self.wait_for_element(self.products_title)
        self.verify_text_equals(self.products_title, expected)
        self.logger.info(f" Verified Products page title: {expected}")

# Alias for backward compatibility
HomePage = ProductsPage

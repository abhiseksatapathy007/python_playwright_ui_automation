from pages.base_page import BasePage
from playwright.sync_api import Page


class CheckoutPage(BasePage):
    """Page object for the Checkout pages (Information, Overview, Complete)."""
    
    def __init__(self, page: Page):
        super().__init__(page)
        # Checkout Information page locators
        self.checkout_info_title = "xpath=//span[@class='title' and text()='Checkout: Your Information']"
        self.first_name_input = "xpath=//input[@id='first-name']"
        self.last_name_input = "xpath=//input[@id='last-name']"
        self.postal_code_input = "xpath=//input[@id='postal-code']"
        self.continue_button = "xpath=//input[@id='continue']"
        self.cancel_button = "xpath=//button[@id='cancel']"
        
        # Checkout Overview page locators
        self.checkout_overview_title = "xpath=//span[@class='title' and text()='Checkout: Overview']"
        self.finish_button = "xpath=//button[@id='finish']"
        
        # Checkout Complete page locators
        self.checkout_complete_title = "xpath=//span[@class='title' and text()='Checkout: Complete!']"
        self.complete_header = "xpath=//h2[@class='complete-header']"
        self.back_home_button = "xpath=//button[@id='back-to-products']"
        
    def verify_checkout_info_page_loaded(self) -> None:
        """Verify the Checkout Information page is loaded."""
        self.wait_for_element(self.checkout_info_title)
        self.logger.info(" Checkout Information page loaded successfully")
    
    def verify_checkout_overview_page_loaded(self) -> None:
        """Verify the Checkout Overview page is loaded."""
        self.wait_for_element(self.checkout_overview_title)
        self.logger.info(" Checkout Overview page loaded successfully")
    
    def verify_checkout_complete_page_loaded(self) -> None:
        """Verify the Checkout Complete page is loaded."""
        self.wait_for_element(self.checkout_complete_title)
        self.logger.info(" Checkout Complete page loaded successfully")
    
    def fill_checkout_information(self, first_name: str, last_name: str, postal_code: str) -> None:
        """
        Fill in checkout information form.
        Args: first_name (str), last_name (str), postal_code (str)
        """
        self.set_text(self.first_name_input, first_name)
        self.set_text(self.last_name_input, last_name)
        self.set_text(self.postal_code_input, postal_code)
        self.logger.info(" Filled checkout information")
    
    def continue_to_overview(self) -> None:
        """Click continue button to proceed to checkout overview."""
        self.click(self.continue_button)
        self.wait_for_page_ready_state()
        self.verify_checkout_overview_page_loaded()
    
    def finish_checkout(self) -> None:
        """Click finish button to complete the checkout."""
        self.click(self.finish_button)
        self.wait_for_page_ready_state()
        self.verify_checkout_complete_page_loaded()
    
    def verify_order_complete(self, expected_message: str = "Thank you for your order!") -> None:
        """Verify the order completion message."""
        self.verify_text_equals(self.complete_header, expected_message)
        self.logger.info(" Order completed successfully")
    
    def back_to_products(self):
        """Click back to products button."""
        self.click(self.back_home_button)
        self.wait_for_page_ready_state()
        from pages.products_page import ProductsPage
        products_page = ProductsPage(self.page)
        products_page.verify_products_page_loaded()
        return products_page


from pages.base_page import BasePage
from playwright.sync_api import Page


class CartPage(BasePage):
    """Page object for the Shopping Cart page."""
    
    def __init__(self, page: Page):
        super().__init__(page)
        # Locators
        self.cart_title = "xpath=//span[@class='title' and text()='Your Cart']"
        self.cart_items = "xpath=//div[@class='cart_item']"
        self.checkout_button = "xpath=//button[@id='checkout']"
        self.continue_shopping_button = "xpath=//button[@id='continue-shopping']"
        self.remove_button_template = "xpath=//div[@class='cart_item'][{index}]//button[contains(@class, 'cart_button')]"
        
    def verify_cart_page_loaded(self) -> None:
        """Verify the Cart page is loaded."""
        self.wait_for_element(self.cart_title)
        self.logger.info(" Cart page loaded successfully")
    
    def get_cart_item_count(self) -> int:
        """Get the number of items in the cart."""
        count = self.page.locator(self.cart_items).count()
        self.logger.info(f"Found {count} items in cart")
        return count
    
    def proceed_to_checkout(self):
        """Click checkout button to proceed to checkout."""
        self.click(self.checkout_button)
        self.wait_for_page_ready_state()
        from pages.checkout_page import CheckoutPage
        checkout_page = CheckoutPage(self.page)
        checkout_page.verify_checkout_info_page_loaded()
        return checkout_page
    
    def continue_shopping(self):
        """Click continue shopping to go back to products page."""
        self.click(self.continue_shopping_button)
        self.wait_for_page_ready_state()
        from pages.products_page import ProductsPage
        products_page = ProductsPage(self.page)
        products_page.verify_products_page_loaded()
        return products_page


from pages.base_page import BasePage
from playwright.sync_api import Page


class ProductsPage(BasePage):
    """Page object for the Products/Inventory page."""
    
    def __init__(self, page: Page):
        super().__init__(page)
        # Locators
        self.products_title = "xpath=//span[@class='title' and text()='Products']"
        self.product_items = "xpath=//div[@class='inventory_item']"
        self.add_to_cart_button_template = "xpath=//div[@class='inventory_item'][{index}]//button[contains(@id, 'add-to-cart')]"
        self.cart_icon = "xpath=//a[@class='shopping_cart_link']"
        self.cart_badge = "xpath=//span[@class='shopping_cart_badge']"
        
    def verify_products_page_loaded(self) -> None:
        """Verify the Products page is loaded."""
        self.wait_for_element(self.products_title)
        self.logger.info(" Products page loaded successfully")
    
    def get_product_count(self) -> int:
        """Get the number of products displayed."""
        count = self.page.locator(self.product_items).count()
        self.logger.info(f"Found {count} products")
        return count
    
    def add_product_to_cart(self, product_index: int = 1) -> None:
        """
        Add a product to cart by index (1-based).
        Args: product_index (int): Product index starting from 1
        """
        button_locator = self.add_to_cart_button_template.format(index=product_index)
        self.click(button_locator)
        self.logger.info(f" Added product {product_index} to cart")
    
    def get_cart_item_count(self) -> int:
        """Get the number of items in the cart from the badge."""
        if self.is_visible(self.cart_badge):
            count_text = self.get_text(self.cart_badge)
            return int(count_text) if count_text.isdigit() else 0
        return 0
    
    def open_cart(self):
        """Click the cart icon to open the shopping cart."""
        self.click(self.cart_icon)
        self.wait_for_page_ready_state()
        from pages.cart_page import CartPage
        cart_page = CartPage(self.page)
        cart_page.verify_cart_page_loaded()
        return cart_page


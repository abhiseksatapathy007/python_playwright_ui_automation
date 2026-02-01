import pytest
from playwright.sync_api import Page
from pages.products_page import ProductsPage
from pages.cart_page import CartPage
from pages.checkout_page import CheckoutPage

"""
Test complete checkout flow: add product, go to cart, checkout, and complete order.
"""
@pytest.mark.ui
@pytest.mark.checkout
@pytest.mark.module("Checkout")
@pytest.mark.usefixtures("apply_scenario_metadata")
def test_complete_checkout_flow(page: Page, scenario):
    products = ProductsPage(page)
    products.verify_products_page_loaded()
    
    # Step 1: Add product to cart
    products.add_product_to_cart(1)
    
    # Step 2: Open cart
    cart = products.open_cart()
    cart.verify_cart_page_loaded()
    
    # Step 3: Proceed to checkout
    checkout = cart.proceed_to_checkout()
    
    # Step 4: Fill checkout information
    checkout.fill_checkout_information(
        first_name=scenario.get("first_name", "John"),
        last_name=scenario.get("last_name", "Doe"),
        postal_code=scenario.get("postal_code", "12345")
    )
    
    # Step 5: Continue to overview
    checkout.continue_to_overview()
    
    # Step 6: Finish checkout
    checkout.finish_checkout()
    
    # Step 7: Verify order completion
    checkout.verify_order_complete()


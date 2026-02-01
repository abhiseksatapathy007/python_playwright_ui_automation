import pytest
from playwright.sync_api import Page
from pages.products_page import ProductsPage
from pages.cart_page import CartPage

"""
Test adding products to cart and verifying cart contents.
"""
@pytest.mark.ui
@pytest.mark.cart
@pytest.mark.module("Cart")
@pytest.mark.usefixtures("apply_scenario_metadata")
def test_add_product_to_cart(page: Page, scenario):
    products = ProductsPage(page)
    products.verify_products_page_loaded()
    
    # Add first product to cart
    products.add_product_to_cart(1)
    
    # Verify cart badge shows 1 item
    cart_count = products.get_cart_item_count()
    assert cart_count == 1, f"Expected 1 item in cart, found {cart_count}"
    
    # Open cart and verify item is present
    cart = products.open_cart()
    item_count = cart.get_cart_item_count()
    assert item_count == 1, f"Expected 1 item in cart, found {item_count}"


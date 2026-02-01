import pytest
from playwright.sync_api import Page
from pages.home_page import HomePage
from pages.products_page import ProductsPage

"""
Verify Products page loads correctly after login.
"""
@pytest.mark.ui
@pytest.mark.home
@pytest.mark.module("Products") # Show this test under "Products" in the email summary
@pytest.mark.usefixtures("apply_scenario_metadata")  # Set test title, description, and severity from the scenario data
def test_verify_products_page_loaded(page: Page):
    products = ProductsPage(page)
    products.verify_products_page_loaded()
    products.wait_for_page_ready_state()
    
    # Verify products are displayed
    product_count = products.get_product_count()
    assert product_count > 0, "No products found on the page"
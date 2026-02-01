import pytest
from playwright.sync_api import Page
from pages.login_page import LoginPage
from pages.home_page import HomePage
from config_utils.config_manager import ConfigManager
from db_utils.query_repository import QueryRepository
from core.test_type import TestType
from core.ui_keys import UIKeys
import logging


@pytest.fixture(scope="function", autouse=True)
def auto_login(page: Page, scenario, request, apply_scenario_metadata):
    """
    Before each test: open base URL, perform login, and assert Products page is visible.
    Fails fast on any error so tests don't run without a valid session.
    """
    logger = logging.getLogger("saucedemo.tests.ui")
    request.node.scenario = scenario

    cfg = ConfigManager(module=TestType.UI)
    base_url = cfg.get(UIKeys.BASE_URL)

    lp = LoginPage(page)

    try:
        lp.open(base_url)
        lp.login(scenario["username"], scenario["password"])
        # Assert session is valid by verifying Products page title
        HomePage(page).verify_home_title("Products")
    except Exception as e:
        logger.error(f"[AutoLogin] Login failed: {e}")
        raise  # fail fast; do not proceed to test body

    # Only yield if setup succeeded
    yield
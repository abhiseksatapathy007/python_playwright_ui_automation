import logging

"""
Lightweight logger helper.

Handlers/formatters are configured once in root `conftest.py`. This helper only
returns a named logger; it does not add handlers (prevents duplicates).
"""

"""
Return a project logger (or named child) without adding handlers.

Args:
  - name (str): Logger name to use. Common patterns:
      - 'saucedemo'                       (project root logger)
      - 'saucedemo.pages.ProductsPage'        (page/class logger)
      - 'saucedemo.tests.ui'              (tests under UI)
      - 'saucedemo.utils.something'       (utility code)

Returns:
  - logging.Logger: Logger instance (handlers configured elsewhere).
"""
def get_logger(name: str = "saucedemo") -> logging.Logger:
    return logging.getLogger(name)
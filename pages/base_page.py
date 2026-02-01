# pages/base_page.py
import logging
import traceback
import base64
import tempfile
from typing import Literal, List, NoReturn
from playwright.sync_api import Page
from utils.ui.screenshot_utils import take_screenshot
import inspect


class UtilityError(Exception):

    """Raised for any failure in base page actions."""
    def __init__(self, utility: str, locator: str, step: str | None, details: str):
        message = f"[{utility}] Step: {step or 'N/A'} | Locator: {locator} | {details}"
        super().__init__(message)

"""
BasePage quick map (flat table)

Note: Locator template = a format-string selector with placeholders (for example, '{row_xpath}', '{row_index}')
that becomes a concrete locator after substitution.

| Method                           | What it does                                  | Signature                                 |
|----------------------------------|-----------------------------------------------|-------------------------------------------|
| click                            | Click an element (waits for visibility)       | click(locator)                            |
| click_by_role                    | Click by ARIA role (optional name)            | click_by_role(role, name=None)            |
| set_text                         | Clear and type into an input                  | set_text(locator, value)                  |
| fill_by_placeholder              | Fill input by placeholder text                | fill_by_placeholder(placeholder, value)   |
| select_dropdown                  | Select <option> by value/label/index          | select_dropdown(locator, value=None,      |
|                                  |                                               |                  label=None, index=None)  |
| wait_for_element                 | Wait for selector state; return Locator       | wait_for_element(locator, state='visible',|
|                                  |                                               |                  timeout=DEFAULT_TIMEOUT) |
| wait_for_page_ready_state        | Wait until network is idle                    | wait_for_page_ready_state()               |
| get_text                         | Get trimmed inner text (waits visible)        | get_text(locator)                         |
| get_value                        | Get input value (waits visible)               | get_value(locator)                        |
| is_visible                       | True/False if visible (soft; no test fail)    | is_visible(locator)                       |
| is_enabled                       | True/False if enabled (soft; no test fail)    | is_enabled(locator)                       |
| verify_text_equals               | Assert element text equals expected           | verify_text_equals(locator, expected)     |
| verify_side_menu_links           | Assert all expected side-menu items visible   | verify_side_menu_links(items,             |
|                                  |                                               |                  locator_template)        |
| select_checkboxes_by_row_indices | Click row checkboxes by 1-based indices       | select_checkboxes_by_row_indices(         |
|                                  |                                               |                  checkbox_xpath_template,  |
|                                  |                                               |                  row_indices)             |
| verify_column_values_by_index    | Assert column index cells equal expected      | verify_column_values_by_index(            |
|                                  |                                               |                  row_locator, column_index,|
|                                  |                                               |                  expected_value,          |
|                                  |                                               |                  row_indices)             |
| verify_rows_cell_values_by_header| Assert cells under header equal expected      | verify_rows_cell_values_by_header(        |
|                                  |                                               |                  row_xpath,               |
|                                  |                                               |                  header_th_xpath_template,|
|                                  |                                               |                  header_text,             |
|                                  |                                               |                  expected_value,          |
|                                  |                                               |                  row_indices)             |
| verify_column_values_by_         | Assert cells by locator template equal        | verify_column_values_by_loctemplate(      |
| loctemplate                      | expected                                      |                  cell_locator_template,   |
|                                  |                                               |                  row_xpath=...,           |
|                                  |                                               |                  expected_value=...,      |
|                                  |                                               |                  row_indices=...)         |
| get_row_indices_by_header_value  | Find rows where cell under header matches     | get_row_indices_by_header_value(          |
|                                  |                                               |                  row_xpath,               |
|                                  |                                               |                  header_th_xpath_template,|
|                                  |                                               |                  header_text,             |
|                                  |                                               |                  expected_value)          |
| get_row_count                    | Return current number of table rows           | get_row_count(row_locator)                |
| row_by_index                     | Build selector to 1-based row index           | row_by_index(row_locator, index)          |
"""

class BasePage:
    """Base class providing reusable Playwright actions with robust error handling."""

    DEFAULT_TIMEOUT = 30000  # single source of truth for waits


    def __init__(self, page: Page):
        """
        Initialize page context and logger.
        Args:
          - page (Page): Playwright page instance for the current test.
        """
        self.page = page
        self.logger = logging.getLogger(f"saucedemo.pages.{self.__class__.__name__}")
        self.current_step: str | None = None


    def _calling_method_name(self) -> str | None:
        """Return the first non-BasePage caller as 'ClassName.method' from the stack for error context."""
        base_methods = set(BasePage.__dict__.keys())
        for fi in inspect.stack()[2:]:  # skip current and direct caller frames
            obj = fi.frame.f_locals.get("self")
            if obj is self:
                fn = fi.function
                if fn not in base_methods:
                    return f"{obj.__class__.__name__}.{fn}"
        return None


    # ---------------- Locator utilities ----------------

    @staticmethod
    def _normalize_locator(locator: str) -> str:
        """
        Normalize raw XPath strings into 'xpath=' selectors; passthrough otherwise.
        Args:
          - locator (str): Any selector; if it starts with '//' or '(//', it is converted to 'xpath=...'.
        """
        locator = locator.strip()
        if locator.startswith("//") or locator.startswith("(//"):
            return f"xpath={locator}"
        return locator


    # ---------------- Wait helpers ----------------
    def wait_for_element(
            self,
            locator: str,
            state: Literal["attached", "detached", "hidden", "visible"] = "visible",
            timeout: int = DEFAULT_TIMEOUT
    ):
        """
        Wait until an element reaches a given state and return its Locator.
        Uses page.wait_for_selector to avoid strict-mode errors on multi-match selectors (e.g., table rows).
        Args:
            - locator (str): Any selector (CSS, xpath=..., etc.). Raw XPath is auto-normalized.
            - state (Literal): 'attached' | 'detached' | 'hidden' | 'visible'. Default 'visible'.
            - timeout (int): Max wait ms; defaults to DEFAULT_TIMEOUT.
        Returns:
            - Locator: Playwright Locator for the element when found.
        """
        normalized = self._normalize_locator(locator)
        try:
            if state != "detached":
                self.page.wait_for_selector(normalized, state="attached", timeout=timeout)
            self.page.wait_for_selector(normalized, state=state, timeout=timeout)
            el = self.page.locator(normalized)
            self.logger.info("Element ready ({}): {}".format(state, locator))
            return el
        except Exception:
            raise


    def wait_for_page_ready_state(self) -> None:
        """
        Wait for the page to reach network idle (ready).
        Args: None
        """
        try:
            self.page.wait_for_load_state("networkidle", timeout=self.DEFAULT_TIMEOUT)
            self.logger.info("Page ready (network idle)")
        except Exception as e:
            self._handle_exception("WaitForPageReadyState", "Page Load", e)


    # ---------------- Element actions ----------------
    def click(self, locator: str):
        """
        Click an element once it is visible.
        Args:
          - locator (str): Selector for the clickable element.
        """
        self.current_step = f"Click - {locator}"
        try:
            el = self.wait_for_element(locator, state="visible")
            el.click()
            self.logger.info(f"Clicked: {locator}")
        except Exception as e:
            self._handle_exception("Click", locator, e)
        finally:
            self.current_step = None


    def set_text(self, locator: str, value: str):
        """
        Clear and set text into an input/textarea.
        Args:
          - locator (str): Selector for the input/textarea.
          - value (str): Text to enter.
        """
        self.current_step = f"Set text '{value}' - {locator}"
        try:
            el = self.wait_for_element(locator, state="visible")
            el.fill("")
            el.fill(value)
            self.logger.info(f"Set text '{value}' in {locator}")
        except Exception as e:
            self._handle_exception("SetText", locator, e)
        finally:
            self.current_step = None


    def select_dropdown(self, locator: str, *, value: str | None = None, label: str | None = None, index: int | None = None):
        """
        Select an option in a native <select> dropdown.
        Args:
          - locator (str): Selector for the <select>.
          - value (str|None): Match by option @value.
          - label (str|None): Match by option visible label.
          - index (int|None): 0-based index.
        Notes:
          - Provide exactly one of value, label, index.
        """
        self.current_step = f"Select dropdown - {locator}"
        try:
            criteria = [v is not None for v in (value, label, index)]
            if sum(criteria) != 1:
                raise ValueError("Provide exactly one of value, label, or index")

            el = self.wait_for_element(locator, state="visible")
            if value is not None:
                el.select_option({"value": value})
            elif label is not None:
                el.select_option({"label": label})
            else:
                el.select_option({"index": index})

            chosen = f"value={value}" if value is not None else (f"label={label}" if label is not None else f"index={index}")
            self.logger.info(f"Selected in dropdown {locator}: {chosen}")
        except Exception as e:
            self._handle_exception("SelectDropdown", locator, e)
        finally:
            self.current_step = None

    # ---------------- Role / Placeholder helpers ----------------
    def click_by_role(self, role: str, name: str | None = None):
        """
        Click an element using ARIA role and accessible name.
        Args:
          - role (str): ARIA role like 'button', 'link'.
          - name (str|None): Accessible name to match (exact).
        """
        label = f"role={role}, name={name}" if name else f"role={role}"
        self.current_step = f"Click by role - {label}"
        try:
            el = self.page.get_by_role(role, name=name) if name else self.page.get_by_role(role)
            el.wait_for(state="visible", timeout=self.DEFAULT_TIMEOUT)
            el.click()
            self.logger.info(f"Clicked by role: {label}")
        except Exception as e:
            self._handle_exception("ClickByRole", label, e)
        finally:
            self.current_step = None

    def fill_by_placeholder(self, placeholder: str, value: str):
        """
        Fill an input located by placeholder attribute.
        Args:
          - placeholder (str): Placeholder attribute to match exactly.
          - value (str): Text to enter.
        """
        locator = f'input[placeholder="{placeholder}"]'
        self.current_step = f"Fill placeholder '{placeholder}' with '{value}'"
        try:
            el = self.wait_for_element(locator, state="visible")
            el.fill(value)
            self.logger.info(f"Filled '{value}' in placeholder '{placeholder}'")
        except Exception as e:
            self._handle_exception("FillByPlaceholder", placeholder, e)
        finally:
            self.current_step = None

    # ---------------- Read utilities ----------------
    def get_text(self, locator: str) -> str:
        """
        Get inner text from a visible element.
        Args:
          - locator (str): Selector for the element.
        """
        self.current_step = f"Get text - {locator}"
        try:
            el = self.wait_for_element(locator, state="visible")
            value = el.inner_text().strip()
            self.logger.info(f"Text from {locator}: {value}")
            return value
        except Exception as e:
            self._handle_exception("GetText", locator, e)


    def get_value(self, locator: str) -> str:
        """
        Get input value from a visible field.
        Args:
          - locator (str): Selector for the input field.
        """
        self.current_step = f"Get value - {locator}"
        try:
            el = self.wait_for_element(locator, state="visible")
            value = el.input_value()
            self.logger.info(f"Value from {locator}: {value}")
            return value
        except Exception as e:
            self._handle_exception("GetValue", locator, e)


    # ---------------- Visibility  Utilities----------------
    def is_visible(self, locator: str) -> bool:
        """
        Check whether an element becomes visible within the default timeout.
        Args:
          - locator (str): Selector for the element.
        """
        self.current_step = f"Check visibility - {locator}"
        try:
            normalized = self._normalize_locator(locator)
            visible = self.page.is_visible(normalized, timeout=self.DEFAULT_TIMEOUT)
            self.logger.info(f"Visibility check for {locator}: {visible}")
            return bool(visible)
        except Exception as e:
            self.logger.info(f"Visibility check for {locator}: False ({e})")
            return False
        finally:
            self.current_step = None


    def is_enabled(self, locator: str) -> bool:
        """
        Check whether an element becomes visible within the default timeout.
        Args:
          - locator (str): Selector for the element.
        """
        self.current_step = f"Check enabled - {locator}"
        try:
            normalized = self._normalize_locator(locator)
            enabled = self.page.is_enabled(normalized, timeout=self.DEFAULT_TIMEOUT)
            self.logger.info(f"Enabled check for {locator}: {enabled}")
            return bool(enabled)
        except Exception as e:
            self.logger.info(f"Enabled check for {locator}: False ({e})")
            return False
        finally:
            self.current_step = None


    # ---------------- Verify utilities ----------------
    def verify_text_equals(self, locator: str, expected: str) -> None:
        """
        Verify that the element's visible text equals the expected text.
        Args:
          - locator (str): Selector for the target element.
          - expected (str): Expected text to compare against.
        Returns: None
        """
        self.current_step = f"Verify text equals - {locator}"
        try:
            actual = self.get_text(locator)
            details = f"Expected: '{expected}'\nActual:   '{actual}'"
            if actual != expected:
                raise AssertionError(f"Text mismatch @ {locator} | expected='{expected}' actual='{actual}'")
            self.logger.info(f"Text match @ {locator}: '{actual}'")
        except Exception as e:
            self._handle_exception("VerifyTextEquals", locator, e)
        finally:
            self.current_step = None


    def verify_side_menu_links(self, expected_menu_items, locator_template):
        """
        Verify that all expected side menu items are visible.

        Args:
          - expected_menu_items (list[str]): Labels to verify in the side menu.
          - locator_template (str): Format string containing '{}' placeholder for the label.
        """
        actual_visible_items = []
        try:
            for item in expected_menu_items:
                locator = locator_template.format(item)
                el = self.wait_for_element(locator, state="visible")
                assert el.is_visible(), f"Menu item '{item}' not visible"
                text = el.inner_text().strip()
                actual_visible_items.append(text)
                self.logger.info(f"Verified menu item: {text}")

            missing = [i for i in expected_menu_items if i not in actual_visible_items]
            if missing:
                raise AssertionError(f"Missing expected menu items: {missing}")

        except Exception as e:
            self._handle_exception("VerifySideMenuLinks", locator_template, e)


    # ---------------- Table utilities ----------------
    def get_row_indices_by_header_value(
            self,
            row_xpath: str,
            header_th_xpath_template: str,
            header_text: str,
            expected_value: str
    ) -> List[int]:
        """
        Return 1-based row indices whose cell under the given header matches expected_value.
        Args:
          - row_xpath (str): Raw XPath selecting all <tr> rows for the grid (no 'xpath=' prefix).
          - header_th_xpath_template (str): Raw XPath template to the <th> element for a header,
                  must contain '{header_text}' placeholder. Example:
                  "//*[@id='grid']/div[1]/div/table/thead/tr/th[normalize-space(.)='{header_text}' or @data-title='{header_text}']"
          - header_text (str): Header text as shown in the grid (e.g., 'Status', 'Assigned To').
          - expected_value (str): Text to compare against (case-insensitive).
        """
        try:
            self.wait_for_page_ready_state()
            self.page.wait_for_timeout(3000)

            rows_el = self.wait_for_element(f"xpath={row_xpath}", state="visible")
            total = rows_el.count()
            self.logger.info("Found {} total rows for row XPath: {}".format(total, row_xpath))

            matched: List[int] = []
            details: List[str] = []
            header_th_xpath = header_th_xpath_template.format(header_text=header_text)

            for i in range(total):
                row_index = i + 1
                cell_locator = (
                    f"xpath=({row_xpath})[{row_index}]/td["
                    f"count({header_th_xpath}/preceding-sibling::th) + 1]"
                )
                cell_el = self.wait_for_element(cell_locator, state="visible")
                text = cell_el.inner_text().strip()
                details.append(f"Row {row_index}: {text}")
                if text.lower() == expected_value.lower():
                    matched.append(row_index)

            if not matched:
                msg = "No rows found where header '{}' = '{}'".format(header_text, expected_value)
                raise AssertionError(msg)

            msg = "Matching rows for '{}' = '{}': {}".format(header_text, expected_value, matched)
            self.logger.info(msg)
            return matched

        except Exception as e:
            self._handle_exception("GetRowIndicesByHeaderValue", header_text, e)


    def select_checkboxes_by_row_indices(self, checkbox_xpath_template, row_indices):
        """
        Click row checkboxes for the provided 1-based row indices.
        Args:
          - checkbox_xpath_template (str): XPath template with '{}' placeholder for the row index.
          - row_indices (list[int]): 1-based row indices to select.
        """
        try:
            for index in row_indices:
                checkbox_locator = checkbox_xpath_template.format(index)
                checkbox_el = self.wait_for_element(checkbox_locator, state="visible")
                checkbox_el.click()
                self.logger.info(f"Selected checkbox in row {index}")

        except Exception as e:
            self._handle_exception("SelectCheckboxesByRowIndices", checkbox_xpath_template, e)


    def verify_column_values_by_index(
            self,
            row_locator: str,
            column_index: int,
            expected_value: str,
            row_indices: list[int],
    ) -> None:
        """
        Verify that cells at a given column index equal expected_value for the given rows.
        Args:
          - row_locator (str): Locator selecting all <tr> rows.
          - column_index (int): 1-based column index to verify.
          - expected_value (str): Expected cell text (case-insensitive).
          - row_indices (list[int]): 1-based rows to check.
        """
        try:
            failed, details = [], []

            for i in row_indices:
                cell_locator = f"{self._normalize_locator(row_locator)}[{i}]/td[{column_index}]"
                cell_el = self.wait_for_element(cell_locator, state="visible")
                actual_text = cell_el.inner_text().strip()
                details.append(f"Row {i}: {actual_text}")
                if actual_text.lower() != expected_value.lower():
                    failed.append(i)

            if failed:
                msg = f"Expected '{expected_value}' but mismatched rows found: {failed}"
                raise AssertionError(msg)

            msg = f"'{expected_value}' correctly found in column {column_index} for rows: {row_indices}"
            self.logger.info(msg)

        except Exception as e:
            self._handle_exception("VerifyColumnValuesByIndex", row_locator, e)


    def verify_rows_cell_values_by_header(
            self,
            row_xpath: str,
            header_th_xpath_template: str,
            header_text: str,
            expected_value: str,
            row_indices: list[int],
    ) -> None:
        """
        Verify that cells under a given header equal expected_value for the given rows (single attempt).
        Args:
          - row_xpath (str): Raw XPath selecting all <tr> rows for the grid (no 'xpath=' prefix).
          - header_th_xpath_template (str): Raw XPath template to the <th> element for a header,
                  must contain '{header_text}' placeholder.
          - header_text (str): Header text (e.g., 'Assigned To', 'Investigator').
          - expected_value (str): Expected cell text (case-insensitive).
          - row_indices (list[int]): 1-based rows to check.
        Returns: None
        Raises:
          - AssertionError: If any row’s value mismatches expected_value.
        """

        # One attempt: allow grid to settle, then read once
        self.wait_for_page_ready_state()
        self.page.wait_for_timeout(2000)

        try:
            failed_rows = []
            details_lines = []
            mismatch_lines = []

            header_th_xpath = header_th_xpath_template.format(header_text=header_text)

            for i in row_indices:
                cell_locator = (
                    f"xpath=({row_xpath})[{i}]/td["
                    f"count({header_th_xpath}/preceding-sibling::th) + 1]"
                )
                cell_el = self.wait_for_element(cell_locator, state="visible")
                actual_text = (cell_el.inner_text() or "").strip()

                details_lines.append(f"Row {i}: expected={repr(expected_value)} | actual={repr(actual_text)}")
                if actual_text.lower() != expected_value.lower():
                    failed_rows.append(i)
                    mismatch_lines.append(f"Row {i}: actual={repr(actual_text)}")

            if failed_rows:
                mismatch_summary = "; ".join(mismatch_lines)
                msg = (
                    f"Expected {repr(expected_value)} under {repr(header_text)} "
                    f"but mismatches in rows {failed_rows}: {mismatch_summary}"
                )
                raise AssertionError(msg)

            msg = f"{repr(expected_value)} found under {repr(header_text)} for rows: {row_indices}"
            self.logger.info(msg)

        except Exception as e:
            self._handle_exception("VerifyRowsCellValuesByHeader", header_text, e)


    def verify_rows_cell_values_by_loctemplate(
            self,
            cell_locator_template: str,
            *,
            row_xpath: str,
            expected_value: str,
            row_indices: list[int],
    ) -> None:
        """
        Verify that, for given row indices, each cell located by template equals expected_value (single attempt).
        Args:
            - cell_locator_template (str): Template with placeholders '{row_xpath}' and '{row_index}'.
            - row_xpath (str): Raw XPath selecting all <tr> rows for the grid (no 'xpath=' prefix).
            - expected_value (str): Expected cell text (case-insensitive).
            - row_indices (list[int]): 1-based row indices to check.
        Returns: None
        Raises:
            - AssertionError: If any row’s cell value does not equal expected_value.
        """
        try:
            self.wait_for_page_ready_state()
            self.page.wait_for_timeout(2000)

            failed_rows, details_lines, mismatch_lines = [], [], []

            for i in row_indices:
                cell_locator = cell_locator_template.format(row_xpath=row_xpath, row_index=i)
                cell_el = self.wait_for_element(cell_locator, state="visible")
                actual = (cell_el.inner_text() or "").strip()
                details_lines.append(f"Row {i}: expected={repr(expected_value)} | actual={repr(actual)}")
                if actual.lower() != expected_value.lower():
                    failed_rows.append(i)
                    mismatch_lines.append(f"Row {i}: actual={repr(actual)}")

            if failed_rows:
                msg = (
                    f"Expected {repr(expected_value)} but mismatches in rows {failed_rows}: "
                    f"{'; '.join(mismatch_lines)}"
                )
                raise AssertionError(msg)

            self.logger.info(f"Verified cell values for rows {row_indices}")

        except Exception as e:
            self._handle_exception("VerifyRowsCellValuesByLocTemplate", cell_locator_template, e)


    # ---------------- Table Small helpers ----------------
    def get_row_count(self, row_locator: str) -> int:
        """
        Get the number of rows matching the provided row locator.
        Args:
            row_locator (str): Locator that selects all <tr> elements for the grid.
        Returns:
            int: The number of rows currently found/visible.
        """
        rows_el = self.wait_for_element(row_locator, state="visible")
        return rows_el.count()


    def row_by_index(self, row_locator: str, index: int) -> str:
        """
        Build a 1-based row locator by combining a base row locator with an index.
        Args:
            row_locator (str): Locator that selects all <tr> elements for the grid.
            index (int): 1-based index of the row to return.
        Returns:
            str: A selector pointing to the specified row.
        """
        return f"{self._normalize_locator(row_locator)}[{index}]"


    # ---------------- Exception handling ----------------
    def _handle_exception(self, step_name: str, locator: str = None, exception: Exception = None) -> NoReturn:
        """
        Take a screenshot, attach diagnostics, log, and raise to fail the test with a concise error.
         Args:
           - step_name (str): Logical step/category where failure happened.
           - locator (str|None): Locator or logical label associated with the failure.
           - exception (Exception|None): Underlying exception to report.
         Returns:
           - NoReturn
         """
        # Build concise error summary
        def _summarize(exc: Exception) -> str:
            if exc is None:
                return "Unknown error"
            only = traceback.format_exception_only(type(exc), exc)
            summary = only[-1].strip() if only else str(exc).strip() or repr(exc)
            return f"{type(exc).__name__}: {summary}" if not summary.startswith(type(exc).__name__) else summary

        # Compose "Action - caller" (e.g., "GetText - verify_home_title")
        caller = (self._calling_method_name() or "").rpartition(".")[2] or "Unknown"
        step_display = f"{step_name} - {caller}"

        summary = _summarize(exception)
        error_message = f"Step: {step_display}\nLocator: {locator}\nError: {summary}"

        try:
            # Take screenshot as Base64 (no file storage)
            base64_screenshot, _ = take_screenshot(self.page, step_name, save_to_file=False)
            if base64_screenshot:
                self.logger.info(f"Screenshot captured for error: {step_name}")
            self.logger.error(error_message)
            self.logger.error(traceback.format_exc())
            
            # Log error to ReportPortal if enabled
            try:
                from utils.reportportal.rp_utils import log_to_rp, is_rp_enabled
                log_to_rp(error_message, level="ERROR")
                log_to_rp(traceback.format_exc(), level="ERROR")
                
                # Note: Screenshot attachment to ReportPortal is handled in conftest.py
                # via the pytest_runtest_makereport hook, so we don't need to attach it here
            except Exception:
                pass  # ReportPortal not available
        finally:
            if isinstance(exception, AssertionError):
                raise exception
            raise AssertionError(error_message)
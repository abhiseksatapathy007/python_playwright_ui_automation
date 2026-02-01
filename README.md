# SauceDemo E-Commerce UI Automation

UI automation framework using Python, Pytest, Playwright and ReportPortal, organized with the Page Object Model (POM). Supports parallel execution, rich HTML reporting, ReportPortal integration, and optional email of results.

## Prerequisites
- Python 3.10+ (project verified on Python 3.13)
- Java 11+ (only if tests query DB via JDBC)
- Git

## 1) Create and activate a virtual environment
```bash
python3 -m venv .venv
source .venv/bin/activate               # macOS/Linux
# On Windows: .venv\Scripts\activate
```

## 2) Install dependencies
```bash
pip install -U pip
pip install -r requirements.txt

# Install Playwright browsers (one-time)
python -m playwright install
```

## 2.5) (Optional) Configure ReportPortal
If you want to use ReportPortal for test reporting:

### Quick Setup

Your ReportPortal is hosted at: **http://your-reportportal-instance.com**

1. **Get your UUID token:**
   ```bash
   # Option 1: Use the helper script
   python3 scripts/get_rp_uuid.py
   
   # Option 2: Manual steps
   # - Open http://your-reportportal-instance.com in browser
   # - Login with your credentials
   # - Go to User Profile > Personal > Copy UUID token
   ```

2. **Configure ReportPortal:**
   
   **Option A: Add to your properties file** (`config/qa.properties`):
   ```properties
   RP_ENABLED=true
   RP_ENDPOINT=http://your-reportportal-instance.com
   RP_PROJECT=SauceDemo-Automation
   RP_UUID=your_uuid_token_here
   RP_LAUNCH_NAME=SauceDemo Test Execution
   RP_ATTACH_SCREENSHOTS=true
   RP_ATTACH_VIDEOS=true
   ```
   
   **Option B: Set environment variables:**
   ```bash
   export RP_ENABLED=true
   export RP_ENDPOINT=http://your-reportportal-instance.com
   export RP_PROJECT=SauceDemo-Automation
   export RP_UUID=your_uuid_token_here
   ```
   
   See `config/reportportal_setup.md` for detailed setup instructions.

## 3) (Optional) DB access via JDBC
If your tests use DB queries, install a JDBC driver (e.g., Microsoft SQL Server):
```bash
mkdir -p "$HOME/jdbc"
curl -fsSL -o "$HOME/jdbc/mssql-jdbc.jar" \
  https://repo1.maven.org/maven2/com/microsoft/sqlserver/mssql-jdbc/12.6.1.jre11/mssql-jdbc-12.6.1.jre11.jar
```
Ensure the driver is discoverable by your environment (e.g., CLASSPATH or project configuration if applicable).

## 4) Configuration
Put UI configuration in:
```
config/qa.properties
```

Example (`config/qa.properties`):
```properties
[DEFAULT]
base.url = https://www.saucedemo.com/
HEADLESS = true
TEST_DATA_PATH = testdata/qa/ui

# Mail (non-sensitive defaults)
GRAPH_API_SCOPE=https://graph.microsoft.com/.default
SUBJECT=SauceDemo: UI Automation Test Execution Summary Report
sendmail=yes

# Database (non-sensitive defaults)
JDBC_DRIVER_PATH=${HOME}/jdbc/mssql-jdbc.jar
JDBC_URL = jdbc:sqlserver://192.168.1.100:1433;databaseName=SampleDatabase;encrypt=false

# Capture Settings
# options: always | failures | never
VIDEO_CAPTURE = failures
SCREENSHOT_CAPTURE = failures
```

### 4.1) Configuration overlays (local secrets)
To keep secrets out of Git, use a local overlay file (already gitignored). Precedence (highest first):
1) `config/qa.local.properties`   (local/secret, not committed)
2) `config/qa.properties`         (committed defaults)

Notes:
- Keep only non-secret defaults (URLs, toggles, paths) in the committed file.
- Put Graph/DB credentials in `qa.local.properties`.

### Security note
- Do not commit credentials. Use `qa.local.properties`.
- If a secret was previously committed, rotate it immediately and consider purging from Git history (e.g., BFG or `git filter-repo`).

## Folder Structure
```text
saucedemo_automation/
├─ run_tests.py
├─ pytest.ini
├─ README.md
├─ conftest.py                  # root pytest hooks (logging, artifacts, etc.)
├─ config/
│  └─ qa.properties             # UI configuration
├─ testdata/
│  └─ qa/
│     └─ ui/
│        ├─ home/
│        │  └─ test_home.json
│        ├─ cart/
│        │  └─ test_cart.json
│        └─ checkout/
│           └─ test_checkout.json
├─ pages/
│  ├─ base_page.py
│  ├─ home_page.py
│  ├─ products_page.py
│  ├─ cart_page.py
│  └─ checkout_page.py
│  └─ investigations_page.py
├─ tests/
│  └─ ui/
│     ├─ conftest.py            # UI-specific fixtures (auto_login, etc.)
│     ├─ test_home.py
│     └─ test_comp_report_assignment.py
├─ utils/
│  ├─ common/
│  │  ├─ send_email.py
│  │  └─ logger.py
│  └─ ui/
│     └─ test_data_loader.py
├─ db_utils/
│  ├─ db_connector.py           # DBUtils: generic JDBC connector + run_query
│  └─ query_repository.py       # QueryRepository: domain query wrappers for tests
├─ config_utils/
│  ├─ config_manager.py
│  └─ property_reader.py
├─ core/
│  ├─ test_type.py
│  └─ ui_keys.py
└─ reports/
   ├─ allure-results/
   ├─ allure-report/
   ├─ videos/
   └─ screenshots/
```

## DB utilities (db_utils)

| Method                           | What it does                                  | Signature                                 |
|----------------------------------|-----------------------------------------------|-------------------------------------------|
| DBUtils.run_query                | Execute parameterized SQL; return rows list    | `run_query(query, params=None) -> list[dict]` |
| fetch_userinfo_by_username       | Get Id, EntityId, UserName, LocationId      | `fetch_userinfo_by_username(username) -> dict` |
| fetch_latest_report_title        | Get latest report UniqueIdentifier             | `fetch_latest_report_title(query=...,`    |
|                                  |                                               | `                 params=[...],`          |
|                                  |                                               | `                 scenario_name=None) -> str` |

## BasePage Cheat Sheet

Note: Locator template = a format-string selector with placeholders (for example, `{row_xpath}`, `{row_index}`) that becomes a concrete locator after substitution.

| Method                           | What it does                                  | Signature                                 |
|----------------------------------|-----------------------------------------------|-------------------------------------------|
| click                            | Click an element (waits for visibility)       | `click(locator)`                          |
| click_by_role                    | Click by ARIA role (optional name)            | `click_by_role(role, name=None)`          |
| set_text                         | Clear and type into an input                  | `set_text(locator, value)`                |
| fill_by_placeholder              | Fill input by placeholder text                | `fill_by_placeholder(placeholder, value)` |
| select_dropdown                  | Select <option> by value/label/index          | `select_dropdown(locator, value=None,`    |
|                                  |                                               | `                 label=None, index=None)` |
| wait_for_element                 | Wait for selector state; return Locator       | `wait_for_element(locator, state='visible',` |
|                                  |                                               | `                 timeout=DEFAULT_TIMEOUT)` |
| wait_for_page_ready_state        | Wait until network is idle                    | `wait_for_page_ready_state()`             |
| get_text                         | Get trimmed inner text (waits visible)        | `get_text(locator)`                       |
| get_value                        | Get input value (waits visible)               | `get_value(locator)`                      |
| is_visible                       | True/False if visible (soft; no test fail)    | `is_visible(locator)`                     |
| is_enabled                       | True/False if enabled (soft; no test fail)    | `is_enabled(locator)`                     |
| verify_text_equals               | Assert element text equals expected           | `verify_text_equals(locator, expected)`   |
| verify_side_menu_links           | Assert all expected side-menu items visible   | `verify_side_menu_links(items,`           |
|                                  |                                               | `                 locator_template)`      |
| select_checkboxes_by_row_indices | Click row checkboxes by 1-based indices       | `select_checkboxes_by_row_indices(`       |
|                                  |                                               | `                 checkbox_xpath_template,` |
|                                  |                                               | `                 row_indices)`           |
| verify_column_values_by_index    | Assert column index cells equal expected      | `verify_column_values_by_index(`          |
|                                  |                                               | `                 row_locator, column_index,` |
|                                  |                                               | `                 expected_value,`        |
|                                  |                                               | `                 row_indices)`           |
| verify_rows_cell_values_by_header| Assert cells under header equal expected      | `verify_rows_cell_values_by_header(`      |
|                                  |                                               | `                 row_xpath,`             |
|                                  |                                               | `                 header_th_xpath_template,` |
|                                  |                                               | `                 header_text,`           |
|                                  |                                               | `                 expected_value,`        |
|                                  |                                               | `                 row_indices)`           |
| verify_column_values_by_         | Assert cells by locator template equal        | `verify_column_values_by_loctemplate(`    |
| loctemplate                      | expected                                      | `                 cell_locator_template,` |
|                                  |                                               | `                 row_xpath=...,`         |
|                                  |                                               | `                 expected_value=...,`    |
|                                  |                                               | `                 row_indices=...)`       |
| get_row_indices_by_header_value  | Find rows where cell under header matches     | `get_row_indices_by_header_value(`        |
|                                  |                                               | `                 row_xpath,`             |
|                                  |                                               | `                 header_th_xpath_template,` |
|                                  |                                               | `                 header_text,`           |
|                                  |                                               | `                 expected_value)`        |
| get_row_count                    | Return current number of table rows           | `get_row_count(row_locator)`              |
| row_by_index                     | Build selector to 1-based row index           | `row_by_index(row_locator, index)`        |

## 5) Test data (per file, method-keyed)
One JSON per test file under:
```
testdata/qa/ui/<module>/<test_file>.json
```
Example (`testdata/qa/ui/home/test_home.json`):
```json
{
  "test_verify_home_side_menu": {
    "scenarios": [
      {
        "name": "Home Page: Side Menu & Sub-Menu ",
        "description": "Verify Home menu and sub-menu",
        "username": "testuser@example.com",
        "password": "******"
      }
    ]
  }
}
```

## 6) How to run
Use the project runner; it cleans artifacts, runs tests, reports to ReportPortal (if enabled), and can send email if enabled.

**Windows:**
```cmd
python run_tests.py -m ui -s
```

**Mac/Linux:**
```bash
python3 run_tests.py -m ui -s
```

**Examples:**

 - Serial – All UI Modules:
   ```cmd
   # Windows
   python run_tests.py --parallel=off -m ui -s
   
   # Mac/Linux
   python3 run_tests.py --parallel=off -m ui -s
   ```
 
 - Serial – Specific Module (e.g., Home):
   ```cmd
   # Windows
   python run_tests.py --parallel=off -m ui -m home -s
   
   # Mac/Linux
   python3 run_tests.py --parallel=off -m ui -m home -s
   ```
 
 - Serial – Single Test File:
   ```cmd
   # Windows
   python run_tests.py --parallel=off tests\ui\home\test_home.py -s
   
   # Mac/Linux
   python3 run_tests.py --parallel=off tests/ui/home/test_home.py -s
   ```
 
 - Parallel – All UI Modules:
   ```cmd
   # Windows
   python run_tests.py -m ui -s
   
   # Mac/Linux
   python3 run_tests.py -m ui -s
   ```
Common markers:
- `ui`, `home`, `cart`, `checkout`

## 7) Reports, artifacts, and logs
- **ReportPortal**: Test results are automatically sent to ReportPortal (if enabled)
- **Local Reports**: `reports/test-results/`
- **Videos**: `reports/videos/`
- **Screenshots**: `reports/screenshots/`
- **Logs** (fresh per run):
  - Serial: `reports/logs/test_execution_log_master.log`
  - Parallel: `reports/logs/test_execution_log_gw<N>.log`

## 8) Emailing the report (optional)
Enable in your UI properties:
```properties
sendmail = yes
```
The sender will:
- Embed a shareable HTML summary
- Use Microsoft Graph API (client credentials)
- Note: ReportPortal reports are accessible via the ReportPortal web interface

Place required credentials in your local overlay file:
- `CLIENT_ID`, `CLIENT_SECRET`, `TENANT_ID`
- `SENDER_EMAIL`, `SEND_EMAIL_URL`, `TO_ADDRESSES`

## 9) Troubleshooting
- Property file not found:
  - Confirm `config/qa.properties` exists.
- Test data file not found:
  - Ensure `TEST_DATA_PATH` is set in `config/qa.properties` and JSON exists per file in the required single format.
- Playwright browser errors:
  - Re-run `python -m playwright install`
- Cleanup before a run (optional):
  - `rm -rf reports/videos reports/screenshots reports/allure-results reports/allure-report`
  - `mkdir -p reports/videos reports/screenshots`

## Quick Start

# 1) Create venv
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# 2) Install deps
pip install -U pip
pip install -r requirements.txt
python -m playwright install

# 3) (Optional) JDBC driver for DB tests
mkdir -p "$HOME/jdbc"
curl -fsSL -o "$HOME/jdbc/mssql-jdbc.jar" \
https://repo1.maven.org/maven2/com/microsoft/sqlserver/mssql-jdbc/12.6.1.jre11/mssql-jdbc-12.6.1.jre11.jar
# Ensure your properties use:
# JDBC_DRIVER_PATH=${HOME}/jdbc/mssql-jdbc.jar

# 4) Config
#   Base (committed): config/qa.properties
#   Local (optional, gitignored): config/qa.local.properties

# 5) Run
python3 run_tests.py -m ui -s
```

## 11) Add a New UI Module and Start Automation of Tests

Follow these steps to add a new UI module and register its pytest marker. Marker names must match your `tests/ui/<module_name>` folder name to avoid “unknown marker” warnings.

1) Create the module folder under `tests/ui/`  
   - Example: create `tests/ui/billing/` and add your test files (e.g., `tests/ui/billing/test_billing_workflow.py`).

2) Update `pytest.ini` to register the module marker  
   - Add a line under `[pytest] -> markers`.  
   - Syntax: `<module_name>: <Human-readable module description>`  
   - Example:
     ```ini
     [pytest]
     markers =
         ui: UI tests
         # Module markers must match tests/ui/<module_name> folders
         billing: Billing module tests
         # Keep if you use @pytest.mark.module("...") for reporting labels
         module(name): Module label for reporting (e.g., 'Products', 'Cart', 'Checkout')
     ```

   3) Tag your tests with markers and a readable module label  
      - In your new test files:
        ```python
        import pytest
        from playwright.sync_api import Page
        from pages.home_page import HomePage 
        import allure
        
        @pytest.mark.ui
        @pytest.mark.billing
        @pytest.mark.module("Billing")
        @pytest.mark.usefixtures("apply_scenario_metadata")
        def test_billing_workflow(page: Page, scenario, request):
            # Optional: expose scenario to hooks / email builder
            request.node.scenario = scenario

            # Example flow
            home = HomePage(page)
            with allure.step("Open Home and verify menus"):
                home.wait_for_page_ready_state()
                home.verify_main_menus_util_admin()
            # TODO: add billing-specific steps here…
        ```

4) Add test data (if applicable)  
   - Create a JSON file under `testdata/qa/ui/<module_name>/`, e.g.:
     ```
     testdata/qa/ui/products/test_products.json
     ```
   - Use the same structure as other UI tests:
     ```json
     {
       "test_billing_workflow": {
         "scenarios": [
           {
            "name": "Add Product to Cart",
            "description": "Verify adding product to cart functionality",
            "username": "standard_user",
            "password": "secret_sauce"
         
           }
         ]
       }
     }
     ``'
5) Run the new module  
   - Serial:
     ```bash
     python3 run_tests.py --parallel=off -m ui -m billing -s
     ```
   - Parallel (default workers):
     ```bash
     python3 run_tests.py -m ui -m billing -s
     ```

## Support
When asking for help, please include:
- Your run command
- The failing test path/marker
- The relevant log: `reports/logs/test_execution_log_*.log`
- A masked screenshot of your UI properties file (no secrets)

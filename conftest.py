# conftest.py
import json
import logging
import os
import re
import shutil
import threading
import jpype
import pytest
import base64
import tempfile
from typing import Any, cast
from playwright.sync_api import ViewportSize
from playwright.sync_api import sync_playwright
from config_utils.property_reader import PropertyReader
from db_utils.db_connector import DBUtils
from utils.common.html_mail_report_utils import (
    get_result_map_list,
    generate_html_table,
)
from utils.ui.screenshot_utils import take_screenshot
from utils.reportportal.rp_config import setup_rp_environment
from core.framework_settings import (
    LOGS_DIR,
    VIDEOS_DIR,
    SCREENSHOTS_DIR,
    TEST_RESULTS_DIR,
    REPORTS_DIR,
    SHAREABLE_REPORT_HTML,
)
from pathlib import Path

# Setup ReportPortal environment before pytest starts
setup_rp_environment()

"""
Pytest root configuration for SauceDemo E-Commerce UI Automation.

Responsibilities:
- Logging: create fresh per-run logs under reports/logs (per worker)
- Reports: clean/recreate videos/screenshots before session
- Playwright lifecycle: session-scoped engine, per-test browser/page with video
- Collection: auto-apply markers/labels from test paths
- Artifacts: on failure attach screenshot/video; finalize shareable HTML on session end
"""

@pytest.fixture(scope="session", autouse=True)
def configure_logging_once():
    """
    Initialize project-wide logging (once per session).
    Files:
    - reports/test_execution_log_<worker>.log (master in serial; gwN in xdist)
    """

    logs_dir = Path(LOGS_DIR)
    logs_dir.mkdir(parents=True, exist_ok=True)

    worker_id = os.getenv("PYTEST_XDIST_WORKER") or "master"
    log_file = logs_dir / f"test_execution_log_{worker_id}.log"

    # Fresh file each run (safe with per-worker filename)
    try:
        if log_file.exists():
            log_file.unlink()
    except Exception:
        pass

    logger = logging.getLogger("saucedemo")
    if getattr(logger, "_configured", False):
        return

    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")

    # File handler (overwrite)
    fh = logging.FileHandler(str(log_file), encoding="utf-8", mode="w")
    fh.setLevel(logging.INFO)
    fh.setFormatter(fmt)

    # Console handler
    sh = logging.StreamHandler()
    sh.setLevel(logging.INFO)
    sh.setFormatter(fmt)

    logger.setLevel(logging.INFO)
    logger.addHandler(fh)
    logger.addHandler(sh)
    logger.propagate = False
    logger._configured = True

    print(f"Logging to: {log_file}")



def _format_mark(mark: str) -> str:
    """
    Format a pytest mark into a display-friendly string.
    Args:
    - mark (str): Raw mark string (e.g., 'cart').
    """
    return mark.replace("_", " ").title()


def resolve_category(keywords):
    """
    Resolve the category (ui) for a test from its keywords.
    Args:
      - keywords (Mapping[str, Any]): Test item keywords/markers.
    Returns:
      - str | None: Resolved category key or None if not found.
    """
    # Prefer explicit parameterized marker: @pytest.mark.category("...")
    cat_mark = keywords.get("category")
    try:
        if cat_mark and getattr(cat_mark, "args", None):
            return str(cat_mark.args[0]).strip()
    except Exception:
        pass
    if "ui" in keywords:
        return "ui"
    return None


def resolve_module(keywords):
    """
    Resolve module name/display for reporting using only the explicit @pytest.mark.module("...").
    Args:
      - keywords (Mapping[str, Any]): Test item keywords/markers (from pytest).
    Returns:
      - tuple[str, str]: (module_key, module_display)
          - module_key: lowercase, underscored version of the display (e.g., 'cart')
          - module_display: original display text (e.g., 'Cart')
    """
    mod_mark = keywords.get("module")
    try:
        if mod_mark and getattr(mod_mark, "args", None):
            display = str(mod_mark.args[0]).strip()
            return display.lower().replace(" ", "_"), display
    except Exception:
        pass
    return "unspecified", "Unspecified"


def pytest_generate_tests(metafunc):
    """
    Auto-parametrize tests that accept a 'scenario' fixture by loading combined JSON from:
    <TEST_DATA_PATH>/<module>/<test_file_stem>.json
        Module is required and inferred from tests/ui/<module>/...
    """
    if 'scenario' in metafunc.fixturenames:
        from pathlib import Path
        import inspect
        from utils.ui.test_data_loader import load_test_data_for_test_name

        test_method = metafunc.function.__name__
        file_path = Path(inspect.getfile(metafunc.function))
        test_file_stem = file_path.stem

        parts = file_path.parts
        if "tests" not in parts:
            raise ValueError(f"Cannot infer module subdir from path: {file_path}")
        i = parts.index("tests")
        if not (len(parts) > i + 2 and parts[i + 1] == "ui"):
            raise ValueError(f"Expected tests/ui/<module>/..., got: {file_path}")
        module_subdir = parts[i + 2]  # e.g., 'cart'

        scenarios = load_test_data_for_test_name(test_file_stem, test_method, module_subdir)
        ids = [f"case{i+1}"] * len(scenarios)
        metafunc.parametrize("scenario", scenarios, ids=ids)


@pytest.fixture
def apply_scenario_metadata(request, scenario):
    """
    Expose the scenario on the node for other hooks.
    Also sets ReportPortal test attributes if enabled.
    """
    request.node.scenario = scenario
    
    # Set ReportPortal test attributes if enabled
    try:
        from utils.reportportal.rp_utils import is_rp_enabled
        if is_rp_enabled():
            # Set test name and description in ReportPortal
            name = (scenario.get("name") or request.node.name).strip()
            desc = (scenario.get("description") or "No description provided").strip()
            
            # ReportPortal will pick up these attributes via pytest-reportportal plugin
            # We can also set them explicitly if needed
            if hasattr(request.node, "user_properties"):
                request.node.user_properties.append(("rp_test_name", name))
                request.node.user_properties.append(("rp_test_description", desc))
    except Exception:
        pass  # ReportPortal not available


def _registered_mark_names(config) -> set[str]:
    """
    Auto-apply markers from directory names under 'tests' (e.g., tests/ui/cart → marks: ui, cart).
    Also infers a readable module label if not explicitly set.
    Args:
      - config (pytest.Config)
      - items (list[pytest.Item])
    """
    names = set()
    for m in config.getini("markers"):
        name = re.split(r"[:(]", m.strip())[0].strip()
        if name:
            names.add(name)
    return names


def pytest_collection_modifyitems(config, items):
    """
    Annotate tests with registered markers from their path and infer a module label.

    - Adds markers found in tests/<category>/<module>/ if registered in pytest.ini (e.g., 'ui', 'home', 'cart').
    - If no @pytest.mark.module("..."), derives it from the second-level dir (e.g., 'cart' -> 'Cart').

    Args: config (pytest.Config), items (list[pytest.Item])
    """
    registered = _registered_mark_names(config)

    for item in items:
        parts = Path(item.fspath).parts
        if "tests" not in parts:
            continue

        idx = parts.index("tests")
        subdirs = list(parts[idx + 1 : -1])  # everything after 'tests', excluding filename

        # Apply any registered markers that match subdirectory names
        for d in subdirs:
            if d in registered:
                item.add_marker(getattr(pytest.mark, d))

        # If no module marker, infer from the second-level dir (e.g., 'cart')
        if not item.get_closest_marker("module"):
            module_dir = subdirs[1] if len(subdirs) >= 2 else (subdirs[0] if subdirs else None)
            if module_dir:
                display = module_dir.replace("_", " ").title()
                item.add_marker(pytest.mark.module(display))


@pytest.hookimpl(tryfirst=True)
def pytest_runtest_setup(item):
    """Setup hook before the test runs."""
    pass

@pytest.hookimpl(tryfirst=True)
def pytest_runtest_call(item):
    """
    Hook during the test call phase.
    """
    pass

# ---------- Failure summarization ----------
def _summarize_failure(report):
    """
    Build a concise failure summary string for reporting/email.
    Args:
      - report (pytest.TestReport): Test report object from pytest hook.
    Returns:
      - str: One-line failure summary (trimmed to ~300 chars).
    """
    try:
        crash = getattr(report.longrepr, 'reprcrash', None)
        if crash and getattr(crash, 'message', None):
            path = getattr(crash, 'path', '')
            lineno = getattr(crash, 'lineno', '')
            message = crash.message.strip()
            base = str(path).split('/')[-1] if path else ''
            return f"{base}:{lineno} - {message}"

        text = getattr(report.longrepr, 'longreprtext', None) or str(report.longrepr)
        lines = [l.rstrip() for l in text.splitlines() if l.strip()]

        e_lines = [l[2:].strip() for l in lines if l.startswith('E ')]
        last_err = e_lines[-1] if e_lines else None

        frame = None
        for l in reversed(lines):
            if 'tests/' in l or 'pages/' in l:
                frame = l.strip()
                break

        waiting = None
        for l in reversed(lines):
            if 'waiting for' in l.lower() or 'Locator.' in l or 'Timeout' in l:
                waiting = l.strip()
                break

        parts = []
        if frame:
            parts.append(frame)
        if last_err:
            parts.append(last_err)
        if waiting and waiting not in parts:
            parts.append(waiting)

        summary = ' | '.join(parts) if parts else (lines[-1] if lines else 'Failure')
        return summary[:300]
    except Exception:
        return 'Failure'


def pytest_addoption(parser):
    """
    Register custom CLI options for this test suite.
    Args:
      - parser (pytest.Parser): Pytest CLI parser.
    """
    parser.addoption(
        "--headed", action="store_true", default=False, help="Run tests in headed mode"
    )
    parser.addoption(
        "--module", action="store", default="SAUCEDEMO", help="Module to run: SAUCEDEMO"
    )


@pytest.fixture(scope="session", autouse=True)
def cleanup_reports_before_session():
    """
    Clean old videos, screenshots, and logs before the test session starts.
    Args: None
    Yields: None
    """
    # Reset videos/screenshots folders
    folders = [
        Path(VIDEOS_DIR),
        Path(SCREENSHOTS_DIR),
    ]

    for folder in folders:
        if folder.exists():
            print(f"Cleaning up old {folder.name} before test run (recursive)...")
            try:
                shutil.rmtree(folder)
                print(f"   Removed: {folder}")
            except Exception as e:
                print(f"   Could not remove {folder}: {e}")
        folder.mkdir(parents=True, exist_ok=True)
        print(f"Created fresh folder: {folder}")

    # Remove previous run logs (master + gwN) to avoid stale content in parallel runs
    logs_dir = Path(LOGS_DIR)
    if logs_dir.exists():
        for p in logs_dir.glob("test_execution_log*.log"):
            try:
                p.unlink()
                print(f"Removed old log: {p}")
            except Exception as e:
                print(f"Could not remove log {p}: {e}")

    yield

# ---------------- JVM Management ----------------

@pytest.fixture(scope="session")
def db_session():
    """
    Provide a shared DBUtils session object (thread-safe).
    Args: None
    Yields:
      - DBUtils: Database utility instance.
    """
    """Provide a single shared DBUtils instance per session (thread-safe)."""
    lock = threading.Lock()
    with lock:
        db = DBUtils()
    yield db


@pytest.fixture(scope="session", autouse=True)
def manage_jvm_once_per_session():
    """
    Start and stop the JVM exactly once per test session.
    Args: None
    Yields: None
    """
    #Start JVM once per session and shut down after all tests complete."""
    db = DBUtils()  # ensures JVM starts once
    print("JVM initialized for DB operations.")
    yield
    if jpype.isJVMStarted():
        try:
            jpype.shutdownJVM()
            print("JVM shutdown successfully after all tests.")
        except Exception as e:
            print(f"JVM shutdown warning: {e}")

# ---------------- Session-scoped Playwright ----------------

@pytest.fixture(scope="session")
def playwright_instance():
    """
    Start Playwright once per session; used by browser/page fixtures.
    Args: None
    Yields:
      - sync_playwright instance (started).
    """
    #Start Playwright once per session for parallel tests."""
    pw = sync_playwright().start()
    yield pw
    pw.stop()

# ---------------- Browser fixture ----------------

@pytest.fixture(scope="function")
def browser(playwright_instance, request):
    """
    Create a Chromium browser instance per test function.
    Args:
      - playwright_instance: Session-scoped Playwright handle.
      - request (pytest.FixtureRequest): Access to CLI opts (e.g., --headed).
    Yields:
      - browser: Playwright Browser instance.
    """
    #Provides a browser instance using session-scoped Playwright."""
    headed = request.config.getoption("--headed")
    slow_mo = 250 if headed else 0
    browser = playwright_instance.chromium.launch(
        headless=not headed,
        slow_mo=slow_mo,
        args=["--start-maximized", "--window-size=1920,1080"]
    )
    yield browser
    browser.close()

# ---------------- Page fixture with video ----------------

@pytest.fixture(scope="function")
def page(browser, request):
    """
    Create a new page/context per test, recording video into worker-specific folders.
    Args:
      - browser: Playwright Browser instance (function-scoped).
      - request (pytest.FixtureRequest): Used to name artifacts and store context/page.
    Yields:
      - page (Page): Playwright Page ready for test actions.
    """
    #Provides a Playwright page with video recording."""
    videos_root = Path(VIDEOS_DIR)
    videos_root.mkdir(parents=True, exist_ok=True)

    # Worker-specific video dir
    worker_id = os.getenv("PYTEST_XDIST_WORKER") or "master"
    worker_videos_dir = videos_root / worker_id
    worker_videos_dir.mkdir(parents=True, exist_ok=True)

    # Nodeid → test_name
    test_name = request.node.nodeid.replace("/", "_").replace("\\", "_").replace(":", "_")
    print(f"Starting test: {test_name}")

    # Start banner
    logging.getLogger("saucedemo").info(f"▶ TEST START: {test_name} (worker={worker_id})")

    # Context with video
    context = browser.new_context(
        viewport=cast(ViewportSize, {"width": 1920, "height": 1080}),
        record_video_dir=str(worker_videos_dir),
        record_video_size=cast(Any, {"width": 1920, "height": 1080}),
    )
    page = context.new_page()

    # Store for hooks
    request.node._test_name = test_name
    request.node._browser_context = context
    request.node._page = page

    yield page

    print(f"Test finished: {test_name}")


@pytest.hookimpl(hookwrapper=True, tryfirst=True)
def pytest_runtest_makereport(item, call):
    """
    Attach screenshot/video artifacts and close browser context after each test call.
    Args:
      - item (pytest.Item): Test node object.
      - call (CallInfo): Call outcome info injected by pytest.
    Yields:
      - None (hookwrapper).
    """
    # Ensure scenario is available for reporting
    try:
        sc = getattr(getattr(item, "callspec", None), "params", {}).get("scenario")
        if isinstance(sc, dict):
            pass  # Scenario available for reporting
    except Exception:
        pass

    outcome = yield
    report = outcome.get_result()

    if report.when != "call":
        return

    test_name = getattr(item, "_test_name", item.nodeid.replace(":", "_").replace("/", "_").replace("\\", "_"))
    logging.getLogger("saucedemo").info(f"TEST END: {test_name} - {report.outcome.upper()}")
    context = getattr(item, '_browser_context', None)
    page_obj = getattr(item, '_page', None)

    screenshots_root = Path(SCREENSHOTS_DIR)

    # --- Read UI configuration from qa.properties ---
    def _get_ui_property(key: str):
        candidates = [
            Path("config") / "qa.local.properties",
            Path("config") / "qa.properties"
        ]
        for p in candidates:
            if p.exists():
                try:
                    reader = PropertyReader(str(p))
                    val = reader.get_property(key)
                    if val is not None:
                        return val
                except Exception:
                    continue
        return None

    VIDEO_CAPTURE = _get_ui_property("VIDEO_CAPTURE")
    SCREENSHOT_CAPTURE = _get_ui_property("SCREENSHOT_CAPTURE")

    # ---------------- Screenshot Handling (before closing context) --------------

    attach_screenshot = (SCREENSHOT_CAPTURE == "always") and page_obj

    if attach_screenshot:
        already_attached = any(
            "screenshot" in (a.name or "").lower()
            for a in getattr(report, "attachments", [])
        )
        if not already_attached:
            try:
                # Take screenshot as Base64 (no file storage needed)
                base64_screenshot, file_path = take_screenshot(page_obj, f"{test_name}_screenshot", save_to_file=False)
                
                if base64_screenshot:
                    print(f"Screenshot captured (Base64)")
                    
                    # Attach Base64 screenshot to ReportPortal
                    try:
                        from utils.reportportal.rp_utils import is_rp_enabled
                        if is_rp_enabled():
                            # Extract base64 data (remove data URI prefix)
                            base64_data = base64_screenshot.split(',', 1)[1] if ',' in base64_screenshot else base64_screenshot
                            
                            # Create temporary file for pytest-reportportal (it expects file paths)
                            # Decode Base64 and write to temp file
                            image_bytes = base64.b64decode(base64_data)
                            with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp_file:
                                tmp_file.write(image_bytes)
                                tmp_path = tmp_file.name
                            
                            # Add to report attachments - pytest-reportportal will handle it
                            if not hasattr(report, 'attachments'):
                                report.attachments = []
                            report.attachments.append((tmp_path, "image/png"))
                    except Exception as e:
                        print(f"Failed to attach screenshot to ReportPortal: {e}")
                else:
                    print(f"Screenshot capture returned empty data")
            except Exception as e:
                print(f"Screenshot capture failed: {e}")
        else:
            print(f"Screenshot already attached for {test_name}, skipping duplicate.")

    # Decide video policy BEFORE closing context
    attach_video = (
                           (VIDEO_CAPTURE == "always") or
                           (VIDEO_CAPTURE == "failures" and report.failed)
                   ) and page_obj and getattr(page_obj, "video", None)

    # Close context so Playwright finalizes the video file
    if context:
        try:
            context.close()
            print(f"Closed browser context for: {test_name}")
        except Exception as e:
            print(f"Could not close context: {e}")

    # Rename every recorded video to the exact test_name inside the worker folder (e.g., reports/videos/master/)
    try:
        src_path = Path(page_obj.video.path())  # e.g., reports/videos/master/<auto>.webm
        if src_path.exists():
            worker_dir = src_path.parent
            dst_path = worker_dir / f"{test_name}.webm"  # tests_ui_...__test_...[...].webm

            if dst_path.exists():
                dst_path.unlink()

            # Prefer atomic move; fall back to copy+delete across filesystems
            try:
                src_path.replace(dst_path)
            except Exception:
                shutil.copy(src_path, dst_path)
                try:
                    src_path.unlink(missing_ok=True)
                except Exception as e:
                    print(f"Could not remove source video: {e}")

            # Video saved per policy (name same for pass/fail)
            if attach_video:
                size = dst_path.stat().st_size
                if size > 1024:
                    print(f"Video saved: {dst_path.name} ({size} bytes)")
                    # Attach video to ReportPortal if enabled
                    # pytest-reportportal automatically picks up attachments from report
                    try:
                        from utils.reportportal.rp_utils import is_rp_enabled
                        if is_rp_enabled():
                            if not hasattr(report, 'attachments'):
                                report.attachments = []
                            report.attachments.append((str(dst_path), "video/webm"))
                    except Exception:
                        pass  # ReportPortal not available or not enabled
                else:
                    print(f"Skipping video - too small ({dst_path.stat().st_size} bytes)")
        else:
            print(f"Video file not found: {src_path}")
    except Exception as e:
        print(f"Video handling failed: {e}")

      # ---------------- Metadata Collection for HTML ----------------

def pytest_sessionfinish(session, exitstatus):
    """
    Finalize email/report metadata (duration and shareable HTML) at session end.
    Args:
      - session (pytest.Session): Current test session.
      - exitstatus (int): Pytest exit status code.
    """
    # Final video summary
    videos_dir = Path(VIDEOS_DIR)
    if videos_dir.exists():
        videos = list(videos_dir.rglob("*.webm"))
        print(f"\nFINAL VIDEO SUMMARY:")
        print(f"   Total videos: {len(videos)}")
        for video in videos:
            size = video.stat().st_size
            status = "OK" if size > 1024 else "FAIL"
            print(f"   {status} {video.name} - {size} bytes")

    # Compute total suite duration (placeholder - can be enhanced with pytest timing)
    formatted_duration = ""
    # Duration calculation can be added using pytest's built-in timing if needed

    # Build shareable HTML + diagnostics
    try:
        reports_dir = Path(REPORTS_DIR)
        reports_dir.mkdir(parents=True, exist_ok=True)

        # Descriptions can be backfilled from test metadata if needed
        name_to_description = {}

        # Generate and write the shareable HTML summary
        html = generate_html_table(get_result_map_list(), formatted_duration=formatted_duration)
        Path(SHAREABLE_REPORT_HTML).write_text(html, encoding="utf-8")
        print("Wrote shareable_report.html for email body")

    except Exception as e:
        print(f"Failed to write shareable report: {e}")
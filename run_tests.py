#!/usr/bin/env python3
"""
One-command test runner for pytest
- Works from project root folder
- Uses relative paths
- Passes headed flag appropriately
- Sends email using UI config
"""

import subprocess
import sys
from pathlib import Path
import shutil
import os
import platform
import json
from datetime import datetime

from config_utils.property_reader import PropertyReader
from utils.reportportal.rp_config import setup_rp_environment

# ---------- Setup ReportPortal (if enabled) ----------
setup_rp_environment()

# ---------- Auto-activate .venv ----------
venv_path = Path(__file__).parent / ".venv"
if venv_path.exists():
    activate_script = venv_path / "bin" / "activate_this.py"
    if activate_script.exists():
        exec(open(activate_script).read(), {"__file__": str(activate_script)})
    sys.executable = str(venv_path / "bin" / "python")

# ---------- Configuration ----------
RESULTS_DIR = Path("reports/test-results")


def get_test_type() -> str:
    """
    Determine active test type: 'ui'.
    Order of precedence:
      1) Marker expression (-m) mentioning ui
      2) Test path hints (tests/ui)
      3) Default: 'ui'
    """
    args = sys.argv[1:]

    # 1) Marker expression: -m ui
    try:
        if "-m" in args:
            idx = args.index("-m")
            if idx + 1 < len(args):
                expr = args[idx + 1].lower()
                if "ui" in expr:
                    return "ui"
    except Exception:
        pass

    # 2) Path hints
    for a in args:
        al = a.lower()
        if "tests/ui" in al or "/ui/" in al or al.endswith("/ui"):
            return "ui"

    # 3) Default
    return "ui"


TEST_TYPE = get_test_type()


def _get_ui_property(key: str):
    """
    Read a UI property from config/qa.properties with optional local overlay.
    Order:
      1) config/qa.local.properties (if exists)
      2) config/qa.properties
    Args:
      - key (str): property key (e.g., 'sendmail').
    Returns:
      - str | None: value or None if not found.
    """
    candidates = [
        Path("config") / "qa.local.properties",
        Path("config") / "qa.properties"
    ]

    for path in candidates:
        if path.exists():
            try:
                reader = PropertyReader(str(path))
                val = reader.get_property(key)
                if val is not None:
                    return val
            except Exception:
                continue
    return None


def run_command(command, description):
    """
    Execute a shell command with logging and basic error handling.
    Args:
    - command (str): Command string to run (shell=True).
    - description (str): Friendly label for logging.
    Returns:
    - bool: True on success; False on failure; True on KeyboardInterrupt.
    """
    print(f"\n{description}...")
    try:
        subprocess.run(command, shell=True, check=True)
        print(f"{description} completed successfully")
        return True
    except subprocess.CalledProcessError:
        print(f"{description} failed.")
        return False
    except KeyboardInterrupt:
        print(f"\n{description} interrupted by user")
        return True


def is_ci():
    """
    Detect CI execution context by environment variables.
    Checks:
      - JENKINS_HOME
      - GITHUB_ACTIONS
      - CI
    Returns:
      - bool: True if any are present; else False.
    """
    ci_vars = ["JENKINS_HOME", "GITHUB_ACTIONS", "CI"]
    return any(os.getenv(var) for var in ci_vars)



def clean_report_directories():
    """
    Clean previous test results and prepare a fresh results directory.
    Actions:
      - Remove reports/test-results if present
      - Recreate reports/test-results
    """
    print("Cleaning previous report data...")

    if RESULTS_DIR.exists():
        shutil.rmtree(RESULTS_DIR)
        print(f"Removed old results: {RESULTS_DIR}")

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)


def write_test_metadata():
    """
    Write test environment metadata to results.
    Files written:
      - environment.properties
    """
    try:
        # Environment
        env_lines = [
            f"OS={platform.platform()}",
            f"Python={platform.python_version()}",
            "Browser=Chromium",
            f"Headed={'false' if is_ci() or '--headless' in ' '.join(sys.argv) else 'true'}",
            f"Environment=QA",
        ]
        (RESULTS_DIR / "environment.properties").write_text("\n".join(env_lines), encoding="utf-8")
    except Exception as e:
        print(f"Failed writing test metadata: {e}")


# ---------- Main ----------
def main():
    """
    Main entry point: parse args/env, run tests, and send email.

    Phases:
      1) Parse --parallel and assemble pytest args
      2) Clean reports; run pytest (xdist optional)
      3) Generate shareable mail body and send email if enabled
    """
    # Collect user args and runner flags
    user_args = []
    # Default parallel: 3 workers unless overridden
    parallel_mode = os.getenv('RUN_PARALLEL', '3').strip().lower() if os.getenv('RUN_PARALLEL') is not None else '3'
    explicit_headed = None
    for arg in sys.argv[1:]:
        if arg.startswith('--parallel='):
            parallel_mode = arg.split('=', 1)[1].strip().lower()
            continue
        if arg in ('--serial', '--no-parallel'):
            parallel_mode = 'off'
            continue
        if arg == '--headed':
            explicit_headed = True
        if arg == '--headless':
            explicit_headed = False
            continue
        user_args.append(arg)
    extra_args = " ".join(user_args)

    # Headed/headless resolution (properties + CLI, CI always headless)
    headless_prop = (_get_ui_property("HEADLESS") or _get_ui_property("headless") or "").strip().lower()
    # explicit_headed is already computed from CLI (--headed / --headless)

    def _is_true(v: str) -> bool:
        return v in ("true", "yes", "1", "headless")

    def _is_false(v: str) -> bool:
        return v in ("false", "no", "0", "headed")

    if is_ci():
        print("CI/CD detected - forcing headless")
        # Strip any accidental --headed
        extra_args = " ".join(a for a in extra_args.split() if a != "--headed")
    else:
        # Respect CLI first
        if explicit_headed is True:
            if "--headed" not in extra_args:
                extra_args += " --headed"
        elif explicit_headed is False:
            # explicit headless → no --headed
            pass
        else:
            # No CLI override → use properties
            if _is_true(headless_prop):
                # headless → no --headed
                pass
            elif _is_false(headless_prop):
                if "--headed" not in extra_args:
                    extra_args += " --headed"
            else:
                # default local: headed
                if "--headed" not in extra_args:
                    extra_args += " --headed"

    # Clean previous reports
    clean_report_directories()
    try:
        hist_dir = RESULTS_DIR / "history"
        if hist_dir.exists():
            shutil.rmtree(hist_dir)
    except Exception:
        pass

    # ---------- Step 1: Run tests ----------
    xdist_args = []
    lower_args = extra_args.lower()
    has_explicit_n = (" -n" in lower_args) or ("--numprocesses" in lower_args)
    has_explicit_dist = ("--dist" in lower_args)

    if not has_explicit_n:
        if parallel_mode == 'off':
            pass
        elif parallel_mode == 'auto' or parallel_mode == '':
            xdist_args.append("-n auto")
        else:
            try:
                num = int(parallel_mode)
                if num > 0:
                    xdist_args.append(f"-n {num}")
            except ValueError:
                xdist_args.append("-n auto")

    # Syntax examples:
    #   parallel=classes/modules (current): --dist=loadscope
    #   parallel=methods (free methods scheduling): remove '--dist=loadscope' or use '--dist=load'
    if not has_explicit_dist and xdist_args:
        xdist_args.append("--dist=loadscope")

    xdist_part = (" " + " ".join(xdist_args)) if xdist_args else ""
    pytest_cmd = f"{sys.executable} -m pytest{xdist_part} {extra_args}"
    print(f"\nRunning tests:\n{pytest_cmd}\n")
    run_command(pytest_cmd, "Running pytest tests")

    # Write test metadata
    write_test_metadata()

    # ---------- Step 2: Send email (even on failure) ----------
    # 2a) Refresh/shareable mail body (HTML table summarizing results)
    try:
        cmd_mail_body = [
            sys.executable,
            "-m",
            "utils.common.custom_mail_report",
            "--results-dir",
            str(RESULTS_DIR),
            "--output",
            "reports/shareable_report.html",
        ]
        # Note: custom_mail_report.py reads from test-results directory
        subprocess.run(cmd_mail_body, check=False)
        print("Refreshed mail body: reports/shareable_report.html")
    except Exception as e:
        print(f"Failed to refresh custom mail report: {e}")

    # 2b) Send email if enabled in UI properties (sendmail=yes/true/1)
    try:
        sendmail_flag = _get_ui_property("sendmail")
        print(f"sendmail flag: {sendmail_flag!r}")

        if (sendmail_flag or "").strip().lower() in ("yes", "true", "1"):
            print("Sending email report...")
            email_script = Path("utils/common/send_email.py")
            if email_script.exists():
                subprocess.run([sys.executable, str(email_script)], check=False)
            else:
                print(f"Email script not found: {email_script}")
        else:
            print("Email disabled (sendmail != yes/true/1 or not set)")

    except Exception as e:
        print(f"Error checking sendmail flag: {e}")
        print("Skipping email due to error")


if __name__ == "__main__":
    main()
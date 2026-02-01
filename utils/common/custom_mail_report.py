#!/usr/bin/env python3
# utils/common/custom_mail_report.py
from __future__ import annotations
from pathlib import Path
from typing import Dict, List, Any, Tuple
from datetime import datetime
import os
import sys
# Ensure project root is on sys.path for direct execution
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from config_utils.config_manager import ConfigManager
from core.ui_keys import UIKeys
from core.test_type import TestType
import argparse
import json


# -------------------- Config: Category/Module resolution from test results --------------------
CATEGORY_SET = {"ui"}
CATEGORY_DISPLAY = {"ui": "UI"}

MODULE_SET = {
    "login",
    "dashboard",
    "profile",
    "reports",
    "example",
}
MODULE_DISPLAY = {
    "login": "Login",
    "dashboard": "Dashboard",
    "profile": "Profile",
    "reports": "Reports",
    "example": "Example",
    "cart": "Cart",
    "checkout": "Checkout",
}

# -------------------- Test result helpers --------------------
def _normalize_status(s: str | None) -> str:
    """Map test status into report status; treat 'broken' as 'failed'."""
    x = (s or "unknown").lower()
    return "failed" if x == "broken" else x

def _ms_to_human(start: int | None, stop: int | None) -> str:
    if not start or not stop or stop < start:
        return ""
    dur = (stop - start) / 1000.0
    if dur < 60:
        return f"{dur:.1f}s"
    m = int(dur // 60)
    s = int(dur % 60)
    return f"{m}m {s}s"

def _load_test_results(results_dir: Path) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    if not results_dir.exists():
        return out
    for f in results_dir.glob("*-result.json"):
        try:
            out.append(json.loads(f.read_text(encoding="utf-8")))
        except Exception:
            pass
    return out

def _load_environment(results_dir: Path) -> Dict[str, str]:
    env: Dict[str, str] = {}
    env_file = results_dir / "environment.properties"
    if env_file.exists():
        try:
            for line in env_file.read_text(encoding="utf-8").splitlines():
                if "=" in line:
                    k, v = line.split("=", 1)
                    env[k.strip()] = v.strip()
        except Exception:
            pass
    if "Environment" not in env:
        env["Environment"] = "QA"
    return env

def _labels_map(t: Dict[str, Any]) -> Dict[str, List[str]]:
    labs: Dict[str, List[str]] = {}
    for l in (t.get("labels") or []):
        n, v = l.get("name"), l.get("value")
        if n and v:
            labs.setdefault(n, []).append(v)
    return labs

def _extract_category_module_from_results(t: Dict[str, Any]) -> Tuple[str, str]:
    labs = _labels_map(t)
    tags = [x.strip() for x in labs.get("tag", [])]

    # Category from known tag
    cat_raw = next((x for x in tags if x in CATEGORY_SET), "")
    category = CATEGORY_DISPLAY.get(cat_raw, (cat_raw or "-"))

    # Module from known tag or explicit labels
    mod_raw = next((x for x in tags if x in MODULE_SET), "")
    if not mod_raw:
        if labs.get("module"):
            mod_raw = labs["module"][0]
        elif labs.get("feature"):
            mod_raw = labs["feature"][0]
        elif labs.get("suite"):
            mod_raw = labs["suite"][0]

    module = MODULE_DISPLAY.get(mod_raw, (mod_raw or "-"))
    return category, module

def _test_title(t):
    labs = _labels_map(t)
    return ((labs.get("display_name") or [t.get("name")])[0]).strip()

def _test_description(t):
    labs = _labels_map(t)
    return ((labs.get("test_description") or [t.get("description") or ""])[0]).strip()

def _status_details(t: Dict[str, Any]) -> Tuple[str, str]:
    msg = (t.get("statusDetails", {}) or {}).get("message") or ""
    trace = (t.get("statusDetails", {}) or {}).get("trace") or ""
    if (not msg and not trace) and t.get("testStage"):
        tsd = (t["testStage"] or {}).get("statusDetails") or {}
        msg = msg or (tsd.get("message") or "")
        trace = trace or (tsd.get("trace") or "")
    return (msg or "").strip(), (trace or "").strip()

def _steps_count(t: Dict[str, Any]) -> int:
    def flat(nodes: List[Dict[str, Any]], acc: List[Dict[str, Any]]):
        for st in nodes:
            acc.append(st)
            if st.get("steps"):
                flat(st["steps"], acc)
    steps = t.get("steps") or (t.get("testStage", {}) or {}).get("steps") or []
    acc: List[Dict[str, Any]] = []
    flat(steps, acc)
    return len(acc)

def _overall_summary(tests: List[Dict[str, Any]]) -> Tuple[int, int, int, int, str]:
    total = len(tests)
    passed = sum(_normalize_status(t.get("status")) == "passed" for t in tests)
    failed = sum(_normalize_status(t.get("status")) == "failed" for t in tests)
    skipped = sum(_normalize_status(t.get("status")) == "skipped" for t in tests)
    starts = [t.get("start") for t in tests if t.get("start")]
    stops = [t.get("stop") for t in tests if t.get("stop")]
    duration = _ms_to_human(min(starts), max(stops)) if (starts and stops) else ""
    return total, passed, failed, skipped, duration

# -------------------- HTML --------------------
def _style() -> str:
    return """
<style>
body { font-family: Verdana, Arial, sans-serif; font-size: 13px; color: #111; margin: 0; background:#f5f6f8; }
.container { max-width: 1400px; margin: 0 auto; padding: 18px 18px 28px 18px; }
.title { background-color:#507963; color:#ffffff; padding:12px; font-size:20px; font-weight:600; text-align:center; display:block; width:100%; margin:0; }
.card { background:#fff; border:1px solid #e7eaef; border-radius:8px; box-shadow: 0 1px 6px rgba(0,0,0,.06); margin-top:16px; overflow:hidden; }
.card h2 { margin:0; padding:12px 14px; font-size:15px; font-weight:800; background:#f7f8fa; border-bottom:1px solid #e7eaef; color:#222; letter-spacing:.2px; display:flex; align-items:center; justify-content:space-between; }
.card .body { padding: 12px 14px; }
.table { width:100%; border-collapse: collapse; }
.table th, .table td { border:1px solid #e3e6eb; padding:8px; font-size:13px; vertical-align: top; }
.table th { background:#7D6655; color:#FCFCFC; text-align:center; font-size:13px; }
.status-pill { padding:2px 8px; border-radius:14px; font-weight:600; color:#000; display:inline-block; }
.pass { background:#99CC66; }
.fail { background:#FF6962; }
.skip { background:#BDC3C7; }
.broken { background:#F5B041; }
.total { background:#A7C7E7; }
.unknown { background:#95A5A6; }
.status-icon { background: transparent !important; padding: 0 !important; border: none !important; box-shadow: none !important; display: inline-block; font-size:16px; line-height:1; }
.no-bold { font-weight:400 !important; }
.center { text-align:center; }
.dim { color:#555; }
</style>
"""

def _status_pill(status: str) -> str:
    s = _normalize_status(status)
    if s == "passed":
        icon = "PASS"
    elif s == "failed":
        icon = "FAIL"
    elif s == "broken":
        icon = "FAIL"
    elif s == "skipped":
        icon = "SKIP"
    else:
        icon = "?"
    # Status text only, no background pill styling for Tests Level Summary
    return f"<span class='status-icon' title='{s.title()}'>{icon}</span>"

def _format_env_display(raw: str) -> str:
    """Normalize environment name for display."""
    if not raw:
        return "Unknown"
    key = raw.strip().lower()
    mapping = {
        "qa": "QA",
        "prod": "Prod",
        "stage": "Stage",
        "stg": "Stg",
        "dev": "Dev",
        "qa": "QA",
        "uat": "UAT",
    }
    return mapping.get(key, raw)

def _discover_report_url(results_dir: Path) -> str | None:
    """Find a hosted report URL from env or executor.json in the given results dir."""
    env_url = os.getenv("TEST_REPORT_URL")
    if env_url and env_url.strip():
        url = env_url.strip().strip('"').strip("'")
        url = url.replace('%22', '')
        while url.endswith('//'):
            url = url[:-1]
        if not url.endswith('/'):
            url += '/'
        return url
    try:
        exec_file = results_dir / "executor.json"
        if exec_file.exists():
            data = json.loads(exec_file.read_text(encoding="utf-8"))
            url = (data or {}).get("reportUrl")
            if url and isinstance(url, str) and url.strip():
                url = url.strip().strip('"').strip("'")
                url = url.replace('%22', '')
                while url.endswith('//'):
                    url = url[:-1]
                if not url.endswith('/'):
                    url += '/'
                return url
    except Exception:
        pass
    return None

def _short_error(msg: str, trace: str) -> str:
    def pick(lines: list[str]) -> str | None:
        for l in lines:
            l = l.strip()
            if l.startswith("AssertionError:") or l.startswith("TimeoutError:"):
                return l
        for l in lines:
            l = l.strip()
            if "Error:" in l:
                return (l.split("Error:", 1)[1] or "").strip() or l
        for l in lines:
            low = l.strip().lower()
            if not (low.startswith("step") or low.startswith("locator:")):
                if l.strip():
                    return l.strip()
        return None

    lines = [x for x in (msg or "").splitlines() if x.strip()]
    trace_lines = [x for x in (trace or "").splitlines() if x.strip()]

    caller = None
    for l in lines:
        if l.lower().startswith("caller:"):
            caller = l.split(":", 1)[1].strip()
            break

    detail = pick(lines) or pick(trace_lines) or "-"
    if caller and detail and caller not in detail:
        return f"{caller} — {detail}"
    return detail or caller or "-"


def build_html(results_dir: Path, title: str) -> str:
    tests = _load_test_results(results_dir)
    env = _load_environment(results_dir)
    total, passed, failed, skipped, duration = _overall_summary(tests)

    row_html: List[str] = []
    for t in sorted(tests, key=lambda x: (_normalize_status(x.get('status')) != 'failed', x.get('name',''))):
        category, module = _extract_category_module_from_results(t)
        name = _test_title(t)
        desc = _test_description(t)
        status = _normalize_status(t.get("status"))
        msg, trace = _status_details(t)
        steps = _steps_count(t)
        # Per-test duration
        start = t.get("start")
        stop = t.get("stop")
        test_duration = _ms_to_human(start, stop) if (start and stop) else ""
        err_short = _short_error(msg, trace)

        row_html.append(
            "<tr>"
            f"<td class='center'>{module}</td>"
            f"<td>{name}</td>"
            f"<td>{(desc or '-')}</td>"
            f"<td class='center'>{steps}</td>"
            f"<td class='center'>{_status_pill(status)}</td>"
            f"<td style='color:{'#D8000C' if err_short != '-' else '#111'};font-weight:500;text-align:{'left' if err_short != '-' else 'center'};'>{err_short}</td>"
            f"<td class='center'>{(test_duration or '-')}</td>"
            "</tr>"
        )

    parts: List[str] = []
    parts.append("<!DOCTYPE html><html><head><meta charset='utf-8'>")
    parts.append(f"<title>{title}</title>")
    parts.append(_style())
    parts.append("</head><body><div class='container'>")

    # Header
    parts.append(f"<h1 class='title'>{title}</h1>")
    # Attachment-first instruction (no hosted URL)
    parts.append(
        "<p class='center' style=\"margin:8px 0 6px; color:#111111; font-size:14px;\">"
        "<strong style='color:#111111;'>Test Report (Detailed):</strong> "
        "<span style='color:#0000ff;'>Please open the attached report</span></p>"
    )

    # Remove standalone Date & Time line below header
    # Remove Environment line as requested

    # No hosted link

    # Overall Summary with right-aligned execution date-time in header
    exec_dt = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    parts.append("<div class='card'><h2>" +
                 "<span>Overall Summary</span>" +
                 f"<span style=\"font-size:13px; font-weight:600; color:#333;\">Execution Date &amp; Time: {exec_dt}</span>" +
                 "</h2><div class='body'>")
    parts.append("<table class='table'>")
    parts.append("<tr><th>Total Tests</th><th>Passed</th><th>Failed</th><th>Skipped</th><th>Duration</th></tr>")
    parts.append(
        "<tr>"
        f"<td class='center'><span class='status-pill total' style=\"font-size:13px; padding:3px 10px;\">{total}</span></td>"
        f"<td class='center'><span class='status-pill pass' style=\"font-size:13px; padding:3px 10px;\">{passed}</span></td>"
        f"<td class='center'><span class='status-pill fail' style=\"font-size:13px; padding:3px 10px;\">{failed}</span></td>"
        f"<td class='center'><span class='status-pill skip' style=\"font-size:13px; padding:3px 10px;\">{skipped}</span></td>"
        f"<td class='center'>{duration or '-'}</td>"
        "</tr>"
    )
    parts.append("</table></div></div>")

    # Tests Level Summary
    parts.append("<div class='card'><h2>Tests Level Summary</h2><div class='body'>")
    parts.append("<table class='table'>")
    parts.append(
        "<tr>"
        "<th>Module</th>"
        "<th>Test Title</th>"
        "<th>Test Description</th>"
        "<th>Steps</th>"
        "<th>Status</th>"
        "<th>Error</th>"
        "<th>Duration</th>"
        "</tr>"
    )
    parts.append("".join(row_html) if row_html else "<tr><td colspan='8' class='center dim'>No tests found</td></tr>")
    parts.append("</table></div></div>")

    # Footer sign-off
    parts.append(
        "<div style=\"margin-top:16px;\">"
        "<p style=\"margin:0; font-size:13px;\">Thanks &amp; Regards,</p>"
        "<p style=\"margin:4px 0 0; font-size:13px;\">Test Automation Team</p>"
        "</div>"
    )

    parts.append("</div></body></html>")
    final_html = "".join(parts)
    return final_html

# -------------------- CLI --------------------
def main():
    parser = argparse.ArgumentParser(description="Build HTML report (header + summary + tests table) from test results.")
    parser.add_argument("--results-dir", default="reports/test-results", help="Path to test results directory")
    parser.add_argument("--output", default="reports/shareable_report.html", help="Output HTML file path")
    parser.add_argument("--title", default=None, help="Header title (fallback to SUBJECT if not provided)")
    args = parser.parse_args()

    results_dir = Path(args.results_dir)
    output = Path(args.output)

    # Title: CLI overrides config SUBJECT; fallback default
    if args.title:
        header_title = args.title
    else:
        try:
            cfg = ConfigManager(module=TestType.UI)
            header_title = cfg.get(UIKeys.SUBJECT)
        except Exception:
            header_title = "SauceDemo Automation Execution Report"

    # Keep header title as-is (do not strip environment suffix)

    html = build_html(results_dir, header_title)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(html, encoding="utf-8")
    print(f"Wrote {output}")

if __name__ == "__main__":
    main()


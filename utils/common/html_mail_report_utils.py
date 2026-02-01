from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path
import os
import json


_result_map_list: List[Dict[str, str]] = []
# _serial_number: int = 1


# def _next_serial_number() -> int:
#     global _serial_number
#     current = _serial_number
#     _serial_number += 1
#     return current


# def send_details_to_open_search(
#     test_name: str,
#     category: Optional[str],
#     test_title: Optional[str],
#     status: str,
#     error: Optional[str] = None,
#     module: Optional[str] = None,
#     test_description: Optional[str] = None,
# ) -> None:
#     """Collect a single test result entry for later HTML table generation.
#
#     - test_name: Typically the pytest node id or test title
#     - category: High-level category (e.g. 'ui')
#     - test_title: Human-readable test title
#     - status: 'pass' | 'fail' | 'skipped'
#     - error: Failure details if any
#     - module: Module mark (e.g. 'login', 'reports'); if provided, used as 'Module Name'
#     """
#
#     entry: Dict[str, str] = {}
#
#     entry["S.No"] = str(_next_serial_number())
#     # Category first, then Module
#     # Use values as provided by tests/config (no forced casing)
#     entry["Category"] = category or ""
#     entry["Module"] = module or (category or "")
#     # Test Title; no separate TestMethod column
#     entry["Test Title"] = test_title or test_name or ""
#     # Title-case for display (Pass/Fail/Skipped)
#     entry["Status"] = (status or "").strip().title()
#     entry["Failure Error"] = ((error or "-").strip() or "-")
#     if test_description:
#         entry["Test Description"] = test_description
#
#     # Timestamp
#     entry["ExecutionTime"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
#
#     _result_map_list.append(entry)


def get_result_map_list() -> List[Dict[str, str]]:
    return _result_map_list


def _discover_report_url() -> Optional[str]:
    """Find a hosted report URL from env or test results executor.json."""
    env_url = os.getenv("TEST_REPORT_URL")
    if env_url and env_url.strip():
        return env_url.strip()
    try:
        exec_file = Path("reports/test-results/executor.json")
        if exec_file.exists():
            data = json.loads(exec_file.read_text(encoding="utf-8"))
            url = (data or {}).get("reportUrl")
            if url and isinstance(url, str) and url.strip():
                return url.strip()
    except Exception:
        pass
    return None


def generate_html_table(map_list: List[Dict[str, str]], report_title: str = "SauceDemo Automation Test Execution Summary Report", formatted_duration: str = "") -> str:
    """Generate an HTML table for email bodies (no hosted link)."""
    html: List[str] = []

    html.append("<div style='font-family: Verdana; font-size: 13px'>")
    html.append("Hi All,<br><br>")
    html.append("Please find the <b>SauceDemo Automation Test Execution Summary Report</b> below.<br><br>")
    html.append("Thanks,<br>Test Automation Team<br><br></div>")

    header = ("<h4 style='color: #0000FF; font-family: Verdana; font-size: 12px'>"
              "[Refer Attachment for Step Wise Results of the Test cases]"
              "</h4>")
    html.append(header)

    html.append("<style>")
    html.append("th { background-color: #7D6655; color: #FCFCFC; text-align: center; font-family: 'Verdana'; font-size: 13px;height: 20px;font-weight: normal; }")
    html.append("td { font-family: 'Verdana'; font-size: 12px; text-align: left; }")
    html.append(".others { background-color: #E5DFD6 !important; color: #000000 !important; }")
    html.append(".pass { background-color: #99CC66 !important; color: #000000 !important; text-align: center !important; }")
    html.append(".fail { background-color: #FF6962 !important; color: #000000 !important;  text-align: center !important; }")
    html.append("</style>")

    html.append("<table border='1' width='100%' style='table-layout:fixed;'>")

    # Title row with duration
    html.append("<tr>")
    html.append(
        "<td colspan='8' style='background-color: #505C45; color: #FFFFFF; font-family: Verdana; font-size: 14px; font-weight: bold; height: 30px;'>"
        "<div style='display: flex; justify-content: space-between; align-items: center;'>"
        f"<span style='flex: 1; text-align: center;'>{report_title}</span>"
        f"<span style='font-size: 13px;'>Total Test Suite Duration: {formatted_duration or ''}</span>"
        "</div>"
        "</td>"
    )
    html.append("</tr>")

    if map_list:
        columns = [
            "S.No", "Category", "Module", "Test Title",
            "Test Description", "Status", "Failure Error", "ExecutionTime",
        ]

        html.append("<tr>")
        for key in columns:
            if key in ("Module", "Test Title", "Test Description"):
                width = "260px"
                html.append(f"<th style='width: {width};'>{key}</th>")
            elif key == "Failure Error":
                html.append("<th style='width: 420px;'>" + key + "</th>")
            else:
                html.append("<th>" + key + "</th>")
        html.append("</tr>")

        for row in map_list:
            html.append("<tr>")
            for key in columns:
                value = row.get(key, "")
                if "error" in key.lower():
                    if value.strip() and value.strip() != "-":
                        html.append("<td style='background-color: #E5DFD6; color: #C30010; text-align: left;'>" + value + "</td>")
                    else:
                        html.append("<td class='others' style='text-align: center;'>-</td>")
                else:
                    if key in ("Category", "Module"):
                        html.append("<td class='others' style='text-align: center;'>" + value + "</td>")
                    elif value.lower() == "fail":
                        html.append("<td class='fail'>" + value + "</td>")
                    elif value.lower() == "pass":
                        html.append("<td class='pass'>" + value + "</td>")
                    else:
                        html.append("<td class='others'>" + value + "</td>")
            html.append("</tr>")

    html.append("</table>")
    return "".join(html)
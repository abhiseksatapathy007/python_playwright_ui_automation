from pathlib import Path
import json
from typing import Any, Dict, List
from config_utils.config_manager import ConfigManager
from core.ui_keys import UIKeys
from core.test_type import TestType


"""
Load test data scenarios for a given UI test method.
Resolution strategy (module-aware via TEST_DATA_PATH + module_subdir):
  - Single JSON per test file (mandatory module subdir):
      <TEST_DATA_PATH>/<module_subdir>/<test_file_stem>.json
      
Required JSON shape (only this format is supported):
  {
    "<test_method_name>": {
      "scenarios": [ { ... }, { ... } ]
    }
  }
Args:
  - test_class_stem (str): Test file stem without extension (e.g., 'test_home').
  - test_method_name (str): Pytest test function name (e.g., 'test_verify_home_side_menu').
  - module_subdir (str): Module folder to append under TEST_DATA_PATH (e.g., 'cart').
Returns:
  - list[dict]: Scenario dictionaries for the given test method.
"""
def load_test_data_for(
        test_class_stem: str,
        test_method_name: str,
        module_subdir: str,
) -> List[Dict[str, Any]]:
    cfg = ConfigManager(module=TestType.UI)
    base = cfg.get(UIKeys.TEST_DATA_PATH)
    if not base:
        raise ValueError("TEST_DATA_PATH not defined in UI properties.")

    if not module_subdir or not isinstance(module_subdir, str):
        raise ValueError("module_subdir is required (e.g., 'cart').")

    base_path = Path(base) / module_subdir
    combined_file = base_path / f"{test_class_stem}.json"
    if not combined_file.is_file():
        raise FileNotFoundError(
            f"Combined test data file not found: {combined_file.resolve()}\n"
            f"   Expected: <TEST_DATA_PATH>/{module_subdir}/{test_class_stem}.json"
        )

    data = json.loads(combined_file.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Invalid JSON structure (root must be an object): {combined_file.resolve()}")

    block = data.get(test_method_name)
    if not isinstance(block, dict):
        raise FileNotFoundError(
            f"No scenarios block found for method '{test_method_name}' in {combined_file.resolve()}\n"
            f"   Required shape:\n"
            f"   {{ \"{test_method_name}\": {{ \"scenarios\": [ ... ] }} }}\n"
        )

    scenarios = block.get("scenarios") or []
    if not isinstance(scenarios, list) or not scenarios:
        raise ValueError(
            f"'scenarios' must be a non-empty list for method '{test_method_name}' in {combined_file.resolve()}"
        )

    return scenarios


"""
Wrapper used by root conftest (module_subdir required).
Args:
  - test_class_stem (str): Test file stem without extension (e.g., 'test_home').
  - test_method_name (str): Pytest test function name (e.g., 'test_verify_home_side_menu').
  - module_subdir (str): Module folder (e.g., 'cart').
Returns:
  - list[dict]: Scenario dictionaries for the given test method.
"""
def load_test_data_for_test_name(
        test_class_stem: str,
        test_method_name: str,
        module_subdir: str
) -> List[Dict[str, Any]]:
    return load_test_data_for(test_class_stem, test_method_name, module_subdir)
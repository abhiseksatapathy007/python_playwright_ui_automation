"""
ReportPortal configuration helper.
Loads ReportPortal settings from environment variables or UI config files.
"""
import os
from config_utils.config_manager import ConfigManager
from core.test_type import TestType
from core.ui_keys import UIKeys


def get_rp_config():
    """
    Get ReportPortal configuration from environment variables or config files.
    
    Returns:
        dict: ReportPortal configuration dictionary
    """
    config = ConfigManager(module=TestType.UI)
    
    # Check if ReportPortal is enabled
    rp_enabled = os.getenv("RP_ENABLED", "").lower()
    if not rp_enabled:
        rp_enabled = (config.get(UIKeys.RP_ENABLED) or "false").lower()
    
    if rp_enabled not in ("true", "yes", "1"):
        return {"enabled": False}
    
    # Get ReportPortal settings
    endpoint = os.getenv("RP_ENDPOINT") or config.get(UIKeys.RP_ENDPOINT) or ""
    
    # Ensure endpoint doesn't have trailing slash
    if endpoint and endpoint.endswith("/"):
        endpoint = endpoint.rstrip("/")
    
    return {
        "enabled": True,
        "endpoint": endpoint,
        "project": os.getenv("RP_PROJECT") or config.get(UIKeys.RP_PROJECT) or "",
        "uuid": os.getenv("RP_UUID") or config.get(UIKeys.RP_UUID) or "",
        "launch_name": os.getenv("RP_LAUNCH_NAME") or config.get(UIKeys.RP_LAUNCH_NAME) or "SauceDemo Test Execution",
        "launch_description": os.getenv("RP_LAUNCH_DESCRIPTION") or config.get(UIKeys.RP_LAUNCH_DESCRIPTION) or "Automated test execution",
        "attach_logs": os.getenv("RP_ATTACH_LOGS", "true").lower() in ("true", "yes", "1"),
        "attach_screenshots": os.getenv("RP_ATTACH_SCREENSHOTS", "true").lower() in ("true", "yes", "1"),
        "attach_videos": os.getenv("RP_ATTACH_VIDEOS", "true").lower() in ("true", "yes", "1"),
    }


def setup_rp_environment():
    """
    Set up ReportPortal environment variables from config.
    This should be called before pytest starts.
    """
    rp_config = get_rp_config()
    
    if not rp_config.get("enabled"):
        return
    
    # Validate required settings
    if not rp_config.get("endpoint"):
        print("ReportPortal enabled but RP_ENDPOINT not configured")
        return
    if not rp_config.get("project"):
        print("ReportPortal enabled but RP_PROJECT not configured")
        return
    if not rp_config.get("uuid"):
        print("ReportPortal enabled but RP_UUID not configured")
        print("   Get your UUID from: ReportPortal UI > User Profile > Personal")
        return
    
    # Set environment variables for pytest-reportportal
    endpoint = rp_config.get("endpoint")
    if endpoint and not endpoint.endswith("/"):
        endpoint = endpoint.rstrip("/")
    
    os.environ["RP_ENDPOINT"] = endpoint
    os.environ["RP_PROJECT"] = rp_config.get("project")
    os.environ["RP_UUID"] = rp_config.get("uuid")
    os.environ["RP_LAUNCH_NAME"] = rp_config.get("launch_name")
    os.environ["RP_LAUNCH_DESCRIPTION"] = rp_config.get("launch_description")
    
    # Enable ReportPortal
    os.environ["RP_ENABLED"] = "true"
    
    print(f"ReportPortal configured: {endpoint} / {rp_config.get('project')}")


"""
ReportPortal integration utilities for SauceDemo E-Commerce UI Automation.
"""
from utils.reportportal.rp_utils import (
    is_rp_enabled,
    get_rp_logger,
    log_to_rp,
    attach_file_to_rp,
    attach_base64_to_rp,
    attach_screenshot_to_rp,
    attach_screenshot_base64_to_rp,
    attach_video_to_rp,
    log_step_to_rp,
)

__all__ = [
    "is_rp_enabled",
    "get_rp_logger",
    "log_to_rp",
    "attach_file_to_rp",
    "attach_base64_to_rp",
    "attach_screenshot_to_rp",
    "attach_screenshot_base64_to_rp",
    "attach_video_to_rp",
    "log_step_to_rp",
]


from core.framework_settings import SCREENSHOTS_DIR
import os
import base64
import datetime
from typing import Optional, Tuple

def take_screenshot(page, name: str, save_to_file: bool = False) -> Tuple[str, Optional[str]]:
    """
    Takes a screenshot and returns it as Base64 encoded string.
    Optionally saves to file if save_to_file is True.
    Also attaches to ReportPortal if enabled.
    
    Args:
        page: Playwright page object
        name: Name identifier for the screenshot
        save_to_file: If True, also save screenshot to local file (default: False)
    
    Returns:
        Tuple[str, Optional[str]]: (base64_encoded_screenshot, file_path_or_none)
            - base64_encoded_screenshot: Base64 encoded PNG image data (data:image/png;base64,...)
            - file_path_or_none: Path to saved file if save_to_file=True, else None
    """
    try:
        # Take screenshot as bytes (in-memory)
        screenshot_bytes = page.screenshot(full_page=True)
        
        # Convert to Base64
        base64_screenshot = base64.b64encode(screenshot_bytes).decode('utf-8')
        base64_data_uri = f"data:image/png;base64,{base64_screenshot}"
        
        file_path = None
        if save_to_file:
            # Optionally save to file for debugging/backup
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            file_name = f"{name}_{timestamp}.png"
            file_path = os.path.join(SCREENSHOTS_DIR, file_name)
            os.makedirs(SCREENSHOTS_DIR, exist_ok=True)
            
            with open(file_path, "wb") as f:
                f.write(screenshot_bytes)
        
        # Attach to ReportPortal if enabled (using Base64)
        try:
            from utils.reportportal.rp_utils import attach_screenshot_base64_to_rp
            attach_screenshot_base64_to_rp(base64_screenshot, name=f"Screenshot - {name}")
        except Exception:
            pass  # ReportPortal not available or not enabled
        
        return base64_data_uri, file_path
    except Exception as e:
        print(f"[WARN] Failed to take screenshot: {e}")
        return "", None


def take_screenshot_base64(page, name: str) -> str:
    """
    Convenience function: Takes a screenshot and returns only Base64 data URI.
    
    Args:
        page: Playwright page object
        name: Name identifier for the screenshot
    
    Returns:
        str: Base64 encoded PNG image data URI (data:image/png;base64,...)
    """
    base64_data_uri, _ = take_screenshot(page, name, save_to_file=False)
    return base64_data_uri


def take_screenshot_file(page, name: str) -> str:
    """
    Legacy function: Takes a screenshot and saves to file (for backward compatibility).
    
    Args:
        page: Playwright page object
        name: Name identifier for the screenshot
    
    Returns:
        str: Path to saved screenshot file
    """
    _, file_path = take_screenshot(page, name, save_to_file=True)
    return file_path or ""

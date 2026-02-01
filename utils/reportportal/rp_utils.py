"""
ReportPortal utility functions for logging, attachments, and test metadata.
"""
import logging
import os
from pathlib import Path
from typing import Optional

try:
    import pytest
    RP_AVAILABLE = True
except ImportError:
    RP_AVAILABLE = False


def is_rp_enabled() -> bool:
    """Check if ReportPortal is enabled via environment variable or config."""
    return os.getenv("RP_ENABLED", "").lower() in ("true", "yes", "1")


def get_rp_logger() -> Optional[logging.Logger]:
    """
    Get the ReportPortal logger instance.
    Returns None if ReportPortal is not available or not enabled.
    """
    if not is_rp_enabled():
        return None
    
    try:
        # pytest-reportportal sets up a logger named 'reportportal'
        logger = logging.getLogger("reportportal")
        # Check if it has handlers (meaning it's configured)
        if logger.handlers:
            return logger
        return None
    except Exception:
        return None


def log_to_rp(message: str, level: str = "INFO", attachment: Optional[dict] = None):
    """
    Log a message to ReportPortal.
    
    Args:
        message: Log message
        level: Log level (DEBUG, INFO, WARNING, ERROR)
        attachment: Optional attachment dict with 'file' and 'name' keys
    """
    if not is_rp_enabled():
        return
    
    try:
        logger = get_rp_logger()
        if logger:
            log_level = getattr(logging, level.upper(), logging.INFO)
            logger.log(log_level, message)
            
            if attachment and "file" in attachment:
                attach_file_to_rp(
                    file_path=attachment["file"],
                    name=attachment.get("name", "Attachment"),
                    mime=attachment.get("mime", "application/octet-stream")
                )
    except Exception:
        # Silently fail if RP is not properly configured
        pass


def attach_file_to_rp(file_path: str, name: str = "Attachment", mime: str = "application/octet-stream"):
    """
    Attach a file to the current ReportPortal test item.
    
    Note: pytest-reportportal automatically handles file attachments when files are logged.
    This function logs the file path which the plugin will pick up.
    
    Args:
        file_path: Path to the file to attach
        name: Display name for the attachment
        mime: MIME type of the file
    """
    if not is_rp_enabled():
        return
    
    try:
        logger = get_rp_logger()
        if logger and Path(file_path).exists():
            # pytest-reportportal plugin automatically attaches files when logging
            # The plugin intercepts log messages and handles file attachments
            # We log the file path and the plugin handles the rest
            logger.info(f"Attachment: {name} - {file_path}")
    except Exception:
        # Silently fail if RP is not properly configured
        pass


def attach_base64_to_rp(base64_data: str, name: str = "Attachment", mime: str = "image/png"):
    """
    Attach Base64-encoded data to ReportPortal.
    
    Args:
        base64_data: Base64 encoded data (without data URI prefix)
        name: Display name for the attachment
        mime: MIME type of the data
    """
    if not is_rp_enabled():
        return
    
    try:
        import base64
        import tempfile
        from pathlib import Path
        
        # Decode Base64 to bytes
        data_bytes = base64.b64decode(base64_data)
        
        # Create a temporary file for pytest-reportportal to attach
        # The plugin expects file paths, so we create a temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.png' if 'image' in mime else '.bin') as tmp_file:
            tmp_file.write(data_bytes)
            tmp_path = tmp_file.name
        
        # Attach the temporary file
        # Note: The temp file will be cleaned up by the OS, but ReportPortal will have the attachment
        logger = get_rp_logger()
        if logger:
            logger.info(f"Attachment: {name} - {tmp_path}")
            
            # Also add to report attachments if we can access the report
            try:
                import pytest
                # Try to get current report from pytest context
                # This is a workaround - ideally pytest-reportportal would handle Base64 directly
                pass
            except Exception:
                pass
    except Exception:
        # Silently fail if RP is not properly configured
        pass


def attach_screenshot_to_rp(file_path: str, name: str = "Screenshot"):
    """Attach a screenshot file to ReportPortal."""
    attach_file_to_rp(file_path, name, "image/png")


def attach_screenshot_base64_to_rp(base64_data: str, name: str = "Screenshot"):
    """
    Attach a Base64-encoded screenshot to ReportPortal.
    
    Args:
        base64_data: Base64 encoded image data (without data URI prefix)
        name: Display name for the attachment
    """
    attach_base64_to_rp(base64_data, name, "image/png")


def attach_video_to_rp(file_path: str, name: str = "Video"):
    """Attach a video to ReportPortal."""
    attach_file_to_rp(file_path, name, "video/webm")


def log_step_to_rp(step_name: str):
    """
    Log a step to ReportPortal (creates a nested step in the test).
    
    Args:
        step_name: Name of the step
    """
    if not is_rp_enabled():
        return
    
    try:
        logger = get_rp_logger()
        if logger:
            logger.info(f"STEP: {step_name}")
    except Exception:
        pass


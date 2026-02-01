# ReportPortal Integration

This directory contains utilities for integrating ReportPortal with the SauceDemo E-Commerce UI Automation framework.

## Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure ReportPortal:**

   You can configure ReportPortal in two ways:

   **Option A: Environment Variables**
   ```bash
   export RP_ENABLED=true
   export RP_ENDPOINT=https://your-reportportal-instance.com
   export RP_PROJECT=your_project_name
   export RP_UUID=your_uuid_token
   export RP_LAUNCH_NAME="SauceDemo Test Execution"
   export RP_LAUNCH_DESCRIPTION="Automated test execution"
   ```

   **Option B: Configuration File**
   
   Add to your properties file (`config/qa.properties`):
   ```properties
   RP_ENABLED=true
   RP_ENDPOINT=https://your-reportportal-instance.com
   RP_PROJECT=your_project_name
   RP_UUID=your_uuid_token
   RP_LAUNCH_NAME=SauceDemo Test Execution
   RP_LAUNCH_DESCRIPTION=Automated test execution
   RP_ATTACH_LOGS=true
   RP_ATTACH_SCREENSHOTS=true
   RP_ATTACH_VIDEOS=true
   ```

## Usage

ReportPortal integration is automatic once configured. The framework will:

- Automatically log test execution to ReportPortal
- Attach screenshots on failures
- Attach videos (if configured)
- Log test steps and actions
- Include test metadata (name, description, severity)

## Manual Logging

You can also manually log to ReportPortal in your tests:

```python
from utils.reportportal import log_to_rp, log_step_to_rp, attach_screenshot_to_rp

# Log a step
log_step_to_rp("Step 1: Navigate to login page")

# Log a message
log_to_rp("User logged in successfully", level="INFO")

# Attach a screenshot
attach_screenshot_to_rp("/path/to/screenshot.png", name="Login Page")
```

## Features

- **Automatic Test Reporting**: Tests are automatically reported to ReportPortal
- **Screenshot Attachments**: Screenshots are captured as Base64 (no local file storage) and automatically attached on failures
- **Video Attachments**: Videos can be attached if configured
- **Step Logging**: Test steps are logged for better traceability
- **Metadata Support**: Test names, descriptions, and severity are included
- **Base64 Screenshots**: Screenshots are stored in-memory as Base64, reducing disk I/O and storage requirements

## Troubleshooting

If ReportPortal is not working:

1. Check that `RP_ENABLED` is set to `true`
2. Verify `RP_ENDPOINT`, `RP_PROJECT`, and `RP_UUID` are correct
3. Ensure `pytest-reportportal` is installed: `pip install pytest-reportportal`
4. Check that your ReportPortal instance is accessible
5. Review pytest output for any ReportPortal-related errors


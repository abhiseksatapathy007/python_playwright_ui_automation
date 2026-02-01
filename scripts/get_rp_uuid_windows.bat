@echo off
REM Windows batch script to help get ReportPortal UUID token
REM This script opens ReportPortal in your browser and provides instructions

echo ======================================================================
echo ReportPortal UUID Token Helper (Windows)
echo ======================================================================
echo.
echo Opening ReportPortal in your default browser...
echo.

start http://your-reportportal-instance.com

echo.
echo ======================================================================
echo Instructions:
echo ======================================================================
echo.
echo 1. Login with your ReportPortal credentials
echo.
echo 2. Get UUID token:
echo    a. Click on your profile icon (top-right corner)
echo    b. Select "User Profile" or "Personal"
echo    c. Find the "UUID" field
echo    d. Copy the UUID (format: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx)
echo.
echo 3. Add to your properties file:
echo    - Edit: config\qa.properties
echo    - Add: RP_UUID=your_copied_uuid_here
echo.
echo ======================================================================
echo.
pause


# ReportPortal Setup Guide

## Your ReportPortal Instance

- **Server URL**: `http://your-reportportal-instance.com` (or `https://your-reportportal-instance.com` if SSL is enabled)
- **Username**: `your_username`
- **Password**: `your_password`

## Step 1: Access ReportPortal and Get UUID Token

### Windows Users (Easiest Method)

**Option 1: Use the batch script (Recommended)**
```cmd
scripts\get_rp_uuid_windows.bat
```
This will open ReportPortal in your browser automatically.

**Option 2: Use the Python script**
```cmd
python scripts\get_rp_uuid_windows.py
```

### Mac/Linux Users

```bash
python3 scripts/get_rp_uuid.py
```

### Manual Steps (All Platforms)

1. **Open your browser and navigate to:**
   ```
   http://your-reportportal-instance.com
   ```
   (or `https://your-reportportal-instance.com` if SSL is configured)

2. **Login with credentials:**
   - Use your ReportPortal credentials

3. **Get your UUID token:**
   - Click on your username/profile icon (usually top-right)
   - Go to **"User Profile"** or **"Personal"**
   - Find the **"UUID"** field - this is your API token
   - **Copy this UUID token** (it looks like: `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`)
   - **Important**: Copy the entire UUID including all dashes, no spaces before or after

## Step 2: Create or Select a Project

1. In ReportPortal, navigate to **Projects**
2. Either:
   - **Select an existing project** (note the project name)
   - **Create a new project** (e.g., "SauceDemo-Automation")

## Step 3: Configure in Your Properties File

Add the following to your properties file (`config/qa.properties`):

```properties
# ReportPortal Configuration
RP_ENABLED=true
RP_ENDPOINT=http://your-reportportal-instance.com
RP_PROJECT=your_project_name_here
RP_UUID=your_uuid_token_here
RP_LAUNCH_NAME=SauceDemo Test Execution
RP_LAUNCH_DESCRIPTION=Automated test execution for SauceDemo E-Commerce UI
RP_ATTACH_LOGS=true
RP_ATTACH_SCREENSHOTS=true
RP_ATTACH_VIDEOS=true
```

**Important:** Replace:
- `your_project_name_here` with your actual project name from Step 2
- `your_uuid_token_here` with the UUID token from Step 1

## Step 4: Test the Configuration

**Windows:**
```cmd
python run_tests.py -m ui tests\ui\home\test_home.py -s
```

**Mac/Linux:**
```bash
python3 run_tests.py -m ui tests/ui/home/test_home.py -s
```

Check your ReportPortal instance to see if the test results appear.

## Troubleshooting

### Connection Issues

If you can't connect to ReportPortal:

1. **Check if the server is accessible:**
   ```bash
   curl http://your-reportportal-instance.com
   ```

2. **Check if SSL is required:**
   - Try `https://your-reportportal-instance.com` instead of `http://`
   - Update `RP_ENDPOINT` accordingly

3. **Check firewall/security groups:**
   - Ensure port 80 (HTTP) or 443 (HTTPS) is open
   - Ensure your IP is allowed to access the EC2 instance

### Authentication Issues

- Verify the UUID token is correct (copy-paste to avoid typos)
- Ensure the username/password work for web login
- Check that the UUID token hasn't expired

### Project Not Found

- Verify the project name in `RP_PROJECT` matches exactly (case-sensitive)
- Ensure you have access to the project in ReportPortal

## Security Note

**Important**: The password and UUID token are sensitive. Consider:
- Using environment variables instead of properties files
- Adding properties files to `.gitignore` if they contain credentials
- Using a secrets management system for production


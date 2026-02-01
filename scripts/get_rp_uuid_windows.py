#!/usr/bin/env python3
"""
Helper script to get ReportPortal UUID token (Windows-friendly).
This script helps you retrieve your UUID token from ReportPortal.

Usage:
    python scripts\get_rp_uuid_windows.py
    OR
    python3 scripts\get_rp_uuid_windows.py

You'll need to:
1. Login to ReportPortal: http://your-reportportal-instance.com
2. Go to User Profile > Personal
3. Copy the UUID token
"""
import requests
import sys
import webbrowser
import os

def get_uuid_from_rp(username: str, password: str, endpoint: str):
    """
    Attempt to verify connection to ReportPortal and open browser.
    """
    print(f"Connecting to ReportPortal at: {endpoint}")
    print(f"Username: {username}")
    print()
    
    # ReportPortal API endpoint for user info
    api_url = f"{endpoint}/api/v1/user"
    
    try:
        # Try to authenticate and get user info
        print("Attempting to verify connection...")
        response = requests.get(
            api_url,
            auth=(username, password),
            timeout=10
        )
        
        if response.status_code == 200:
            user_data = response.json()
            print("Successfully connected to ReportPortal!")
            print(f"   User: {user_data.get('fullName', username)}")
            print(f"   Email: {user_data.get('email', 'N/A')}")
            print()
            return True
        else:
            print(f"Connection status: {response.status_code}")
            print("   This might be normal if the API requires different authentication.")
            print("   Proceed with manual steps below.")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"Cannot connect to {endpoint}")
        print("   Please check:")
        print("     - Is the server running?")
        print("     - Is the URL correct? (try http:// or https://)")
        print("     - Is the server accessible from your network?")
        return False
    except Exception as e:
        print(f"Connection check failed: {e}")
        print("   This might be normal. Proceed with manual steps.")
        return False


if __name__ == "__main__":
    print("=" * 70)
    print("ReportPortal UUID Token Helper (Windows)")
    print("=" * 70)
    print()
    
    # Your ReportPortal instance
    endpoint = os.getenv("RP_ENDPOINT", "http://your-reportportal-instance.com")
    username = os.getenv("RP_USERNAME", "your_username")
    password = os.getenv("RP_PASSWORD", "your_password")
    
    print("Note: Set RP_ENDPOINT, RP_USERNAME, and RP_PASSWORD environment variables")
    print("      or edit this script to set your ReportPortal credentials.")
    print()
    
    # Verify connection
    connected = get_uuid_from_rp(username, password, endpoint)
    
    print()
    print("=" * 70)
    print("Manual Steps to Get UUID (Windows)")
    print("=" * 70)
    print()
    print("1. Opening ReportPortal in your default browser...")
    print()
    
    # Open browser automatically
    try:
        webbrowser.open(endpoint)
        print(f"   Opened: {endpoint}")
    except Exception as e:
        print(f"   Could not open browser automatically: {e}")
        print(f"   Please manually open: {endpoint}")
    
    print()
    print("2. Login with your ReportPortal credentials")
    print()
    print("3. Get UUID token:")
    print("   a. Click on your profile icon (top-right corner)")
    print("   b. Select 'User Profile' or 'Personal'")
    print("   c. Find the 'UUID' field")
    print("   d. Copy the UUID (format: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx)")
    print()
    print("4. Use the UUID in your properties file:")
    print("   - Edit: config\\qa.properties")
    print("   - Add: RP_UUID=your_copied_uuid_here")
    print()
    print("=" * 70)
    print()
    print("Press Enter after you've copied the UUID...")
    try:
        input()
    except KeyboardInterrupt:
        print("\nExiting...")
        sys.exit(0)
    
    print()
    print("Next step: Add the UUID to your configuration file!")
    print("   See: config/reportportal_setup.md for details")


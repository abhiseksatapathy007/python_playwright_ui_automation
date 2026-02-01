#!/usr/bin/env python3
"""
Helper script to get ReportPortal UUID token.
This script helps you retrieve your UUID token from ReportPortal.

Usage:
    python3 scripts/get_rp_uuid.py

You'll need to:
1. Login to ReportPortal: http://your-reportportal-instance.com
2. Go to User Profile > Personal
3. Copy the UUID token
"""
import requests
import sys
import os

def get_uuid_from_rp(username: str, password: str, endpoint: str):
    """
    Attempt to get UUID token from ReportPortal API.
    
    Note: This is a helper. The UUID is typically obtained from the UI.
    """
    print(f"Connecting to ReportPortal at: {endpoint}")
    print(f"Username: {username}")
    
    # ReportPortal API endpoint for user info
    api_url = f"{endpoint}/api/v1/user"
    
    try:
        # Try to authenticate and get user info
        response = requests.get(
            api_url,
            auth=(username, password),
            timeout=10
        )
        
        if response.status_code == 200:
            user_data = response.json()
            print("\nSuccessfully connected to ReportPortal!")
            print(f"User: {user_data.get('fullName', username)}")
            print(f"Email: {user_data.get('email', 'N/A')}")
            print("\nUUID token is not returned by the API for security reasons.")
            print("Please get it manually from the ReportPortal UI:")
            print("  1. Login to ReportPortal")
            print("  2. Click on your profile (top-right)")
            print("  3. Go to 'User Profile' > 'Personal'")
            print("  4. Copy the UUID token")
            return None
        else:
            print(f"Failed to connect. Status: {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except requests.exceptions.ConnectionError:
        print(f"Cannot connect to {endpoint}")
        print("Please check:")
        print("  - Is the server running?")
        print("  - Is the URL correct? (try http:// or https://)")
        print("  - Is the server accessible from your network?")
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None


if __name__ == "__main__":
    print("=" * 60)
    print("ReportPortal UUID Token Helper")
    print("=" * 60)
    print()
    
    # Your ReportPortal instance
    endpoint = os.getenv("RP_ENDPOINT", "http://your-reportportal-instance.com")
    username = os.getenv("RP_USERNAME", "your_username")
    password = os.getenv("RP_PASSWORD", "your_password")
    
    print("Attempting to verify connection to ReportPortal...")
    print()
    print("Note: Set RP_ENDPOINT, RP_USERNAME, and RP_PASSWORD environment variables")
    print("      or edit this script to set your ReportPortal credentials.")
    print()
    
    uuid = get_uuid_from_rp(username, password, endpoint)
    
    print()
    print("=" * 60)
    print("Manual Steps to Get UUID:")
    print("=" * 60)
    print(f"1. Open browser: {endpoint}")
    print("2. Login with your ReportPortal credentials")
    print("3. Click on your profile icon (top-right)")
    print("4. Go to 'User Profile' > 'Personal'")
    print("5. Find and copy the 'UUID' field")
    print("6. Use this UUID in your properties file as RP_UUID")
    print()


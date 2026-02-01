#!/usr/bin/env python3
# Email Test Report Script
# - Loads UI email configuration from properties via ConfigManager(TestType.UI)
# - Builds a shareable HTML email body
# - Sends email using Microsoft Graph API (client credentials flow)

import os
import json
import base64
import requests
from pathlib import Path
from typing import Optional, Union

import sys
# Ensure project root is on sys.path for direct execution
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from config_utils.config_manager import ConfigManager
from core.ui_keys import UIKeys
from core.test_type import TestType


class EmailSender:
    """
    Initialize EmailSender and load UI email configuration.

    Args:
      - None
    """
    def __init__(self):
        self.config = ConfigManager(module=TestType.UI)

        # Microsoft Graph API configuration
        self.client_id = self.config.get(UIKeys.CLIENT_ID)
        self.client_secret = self.config.get(UIKeys.CLIENT_SECRET)
        self.tenant_id = self.config.get(UIKeys.TENANT_ID)
        self.sender_email = self.config.get(UIKeys.SENDER_EMAIL)
        self.send_email_url = self.config.get(UIKeys.SEND_EMAIL_URL)
        self.subject = self.config.get(UIKeys.SUBJECT)

        # Recipients
        to_addresses_str = (self.config.get(UIKeys.TO_ADDRESSES) or "").strip()
        self.to_addresses = [e.strip() for e in to_addresses_str.split(",") if e.strip()]

        # Graph API scope (e.g., "https://graph.microsoft.com/.default")
        self.graph_api_scope = self.config.get(UIKeys.GRAPH_API_SCOPE)

        print("Email configuration loaded:")
        print(f"   Sender: {self.sender_email}")
        print(f"   Recipients: {', '.join(self.to_addresses) if self.to_addresses else '(none)'}")
        print(f"   Subject: {self.subject}")

    """
    Read a file and return its Base64-encoded content as a UTF-8 string.

    Args:
      - file_path (str | Path): Path of the file to encode.

    Returns:
      - str: Base64 string (Graph API expects string for 'contentBytes').
    """
    @staticmethod
    def encode_file_to_base64(file_path: Union[str, Path]) -> str:
        with open(file_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")

    """
    Obtain an OAuth2 access token (client-credentials) for Microsoft Graph.

    Args:
      - None

    Returns:
      - str: Bearer token for Microsoft Graph API

    Raises:
      - requests.HTTPError: If token acquisition fails.
    """
    def get_access_token(self) -> str:
        token_url = f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token"
        data = {
            "client_id": self.client_id,
            "scope": self.graph_api_scope,
            "client_secret": self.client_secret,
            "grant_type": "client_credentials",
        }
        print("Getting access token...")
        response = requests.post(token_url, data=data)
        response.raise_for_status()
        token_data = response.json()
        print("Access token obtained successfully")
        return token_data["access_token"]

    """
    Build the Microsoft Graph API email payload as a JSON string.

    Args:
      - to_addresses (list[str]): Recipient email addresses.
      - subject (str): Email subject line.
      - html_body (str): Email HTML content.
      - attachments (list[dict] | None): Optional Graph API attachments.

    Returns:
      - str: JSON payload string to POST to Graph API.
    """
    @staticmethod
    def construct_email_payload(
            to_addresses: list[str],
            subject: str,
            html_body: str,
            attachments: Optional[list[dict]] = None
    ) -> str:
        if not subject:
            subject = "No Subject"
        recipients = [{"emailAddress": {"address": addr.strip()}} for addr in to_addresses]
        payload = {
            "message": {
                "subject": subject,
                "body": {"contentType": "HTML", "content": html_body},
                "toRecipients": recipients,
            },
            "saveToSentItems": True,
        }
        if attachments:
            payload["message"]["attachments"] = attachments
        return json.dumps(payload)

    """
    Send the prepared email payload via Microsoft Graph API.

    Args:
      - access_token (str): OAuth bearer token.
      - payload_json (str): JSON payload from construct_email_payload.

    Returns:
      - bool: True if Graph returns HTTP 202; else False.
    """
    def send_email_via_graph_api(self, access_token: str, payload_json: str) -> bool:
        headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
        print("Sending email via Microsoft Graph API...")
        response = requests.post(self.send_email_url, headers=headers, data=payload_json)
        if response.status_code == 202:
            print("Email sent successfully via Microsoft Graph API.")
            return True
        print(f"Error sending email. Response code: {response.status_code}")
        print(f"Response message: {response.reason}")
        print(f"Response body: {response.text}")
        return False

    """
    Build HTML body from shareable_report.html and send to configured recipients via Graph API.

    Args:
      - None

    Returns:
      - bool: True on success, False otherwise.

    Notes:
      - Requires 'reports/shareable_report.html'.
    """
    def send_test_report_email(self) -> bool:
        try:
            attachments: list[dict] = []

            # Required: shareable HTML table body
            shareable_table_path = Path("reports/shareable_report.html")
            if not shareable_table_path.exists():
                raise FileNotFoundError(
                    "reports/shareable_report.html not found. Ensure tests completed and report was generated."
                )
            print(f"Using shareable HTML table: {shareable_table_path}")
            html_body = shareable_table_path.read_text(encoding="utf-8")

            if not self.to_addresses:
                raise ValueError("No recipient addresses configured (TO_ADDRESSES)")

            access_token = self.get_access_token()
            payload = self.construct_email_payload(self.to_addresses, self.subject, html_body, attachments or None)
            return self.send_email_via_graph_api(access_token, payload)

        except Exception as e:
            print(f"Failed to send test report email: {e}")
            return False


"""
CLI entrypoint to send the test report email.

Args:
  - None

Exit codes:
  - 0 on success; 1 on failure (for CI visibility).
"""
def main():
    print("Send Test Report via Email")
    print("=" * 40)
    try:
        sender = EmailSender()
        ok = sender.send_test_report_email()
        if ok:
            print("\nEmail sent successfully!")
        else:
            print("\nFailed to send email")
            exit(1)
    except Exception as e:
        print(f"Error: {e}")
        exit(1)


if __name__ == "__main__":
    main()
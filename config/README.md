Config structure and precedence (highest first)

1) config/qa.local.properties   # local/secret overlay (ignored)
2) config/qa.properties          # base defaults (safe)

Guidelines
- Commit only non-secret defaults (URLs, toggles, paths).
- Put real secrets (usernames, passwords, JDBC creds) ONLY in qa.local.properties (gitignored).
- Local overlays are optional; if absent, the framework falls back to committed defaults.

Common keys (examples)
- UI (non-secret):
  - BASE_URL
  - VIDEO_CAPTURE (always|failures|off)
  - SCREENSHOT_CAPTURE (always|failures|off)
  - SUBJECT (email/report title)
  - TEST_DATA_PATH (e.g., testdata/qa/ui)
- Secrets (local only):
  - USERNAME, PASSWORD
  - DB_JDBC_URL, DB_USER, DB_PASSWORD

Local setup
- Create local overlay as needed:
  - config/qa.local.properties

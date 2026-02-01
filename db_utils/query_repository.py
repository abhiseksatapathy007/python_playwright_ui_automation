from db_utils.db_connector import DBUtils

class QueryRepository:
    """
    Central place for domain-specific DB queries used by UI tests.

    - Wraps DBUtils.run_query(...) with readable methods (e.g., fetch_latest_report_title).
    - Keeps SQL and parameter assembly in one location (no DB logic in Page Objects).
    - Adds fail-fast assertions close to the query intent.
    - Encourages reuse and clearer test code: tests call repo → repo calls DBUtils.
    """
    def __init__(self):
        self.db = DBUtils()

    def fetch_userinfo_by_username(self, username: str) -> dict:
        """
        Get Id, EntityId, UserName, LocationId for a user.
        Args: username (str)  Returns: dict with those keys
        """
        rows = self.db.run_query(
            "SELECT Id, EntityId, UserName, LocationId FROM [User] WHERE UserName = ?",
            [username],
        )
        assert rows, f"No user found for '{username}'"
        user = rows[0]
        return user


    def fetch_latest_report_title(self, *, query: str, params: list[str], scenario_name: str = "") -> str:
        """
        Get latest report title. Args: query, params, scenario_name. Returns: str
        """
        rows = self.db.run_query(query, params)
        assert rows, f"No report found for scenario: {scenario_name or '(unknown)'}"
        title = str(rows[0]["UniqueIdentifier"])
        return title
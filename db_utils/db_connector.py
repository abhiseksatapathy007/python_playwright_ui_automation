import jpype
import jpype.imports
import logging
import threading
from config_utils.config_manager import ConfigManager
from core.test_type import TestType
from core.ui_keys import UIKeys
from jpype import JException  # at top of file
from typing import Optional, Any


class DBUtils:
    """
    Utility class to connect to SQL Server using JDBC and run parameterized queries.
    Thread-safe version for parallel test execution.
    """
    _jvm_message_shown = False        # flag to ensure message is printed once
    _jvm_lock = threading.Lock()      # lock to make JVM startup thread-safe

    def __init__(self):
        self.logger: logging.Logger = logging.getLogger("saucedemo.db")
        self.config = ConfigManager(module=TestType.UI)
        self.jdbc_driver_path = self.config.get(UIKeys.JDBC_DRIVER_PATH)
        self.jdbc_url = self.config.get(UIKeys.JDBC_URL)
        self.user = self.config.get(UIKeys.DB_USER)
        self.password = self.config.get(UIKeys.DB_PASSWORD)

        # ensure JVM is started only once (thread-safe)
        self._ensure_jvm_started()

        from jpype import JClass
        self.DriverManager = JClass("java.sql.DriverManager")
        self.SQLException = JClass("java.sql.SQLException")
        self.PreparedStatement = JClass("java.sql.PreparedStatement")


    def _ensure_jvm_started(self):
        """Start JVM safely only once, even when called from multiple threads."""
        with DBUtils._jvm_lock:
            if not jpype.isJVMStarted():
                print("⚡ Starting JVM...")
                jpype.startJVM(
                    jpype.getDefaultJVMPath(),
                    "-ea",
                    classpath=[self.jdbc_driver_path]
                )
                DBUtils._jvm_message_shown = True
            else:
                if not DBUtils._jvm_message_shown:
                    print("🟢 JVM already running.")
                    DBUtils._jvm_message_shown = True


    def run_query(self, query: str, params: list | None = None) -> list[dict]:
        """
        Execute a SQL query and return rows as list[dict].
        Args:
          - query (str): SQL with optional '?' placeholders.
          - params (list|None): Values for placeholders in order.
        Returns:
          - list[dict]: Each row as {column_name: value} (strings).
        """
        self._ensure_jvm_started()
        conn = stmt = rs = None
        try:
            # 1) Open connection
            conn = self.DriverManager.getConnection(self.jdbc_url, self.user, self.password)
            if params:
                stmt = conn.prepareStatement(query)
                for i, val in enumerate(params):
                    stmt.setString(i + 1, str(val) if val is not None else None)
                rs = stmt.executeQuery()          # PreparedStatement execution
            else:
                stmt = conn.createStatement()
                rs = stmt.executeQuery(query)     # Statement execution
                # rs (java.sql.ResultSet) logical view before conversion:
                # Columns: [UniqueIdentifier, Title, ...]
                # Rows:
                #   Row 1 → UniqueIdentifier="2025-11-15_ABC123", Title="Order Report", ...
                #   Row 2 → UniqueIdentifier="2025-11-14_DEF456", Title="Order Report", ...

            # 2) Convert ResultSet → list[dict]
            results = self._resultset_to_dicts(rs)
            self.logger.info(f"DB rows: {len(results)}")
            return results

        except (self.SQLException, JException) as e:
            msg = f"DB connection/query failed (JDBC): {e}"
            self.logger.error(msg)
            raise AssertionError(msg)
        finally:
            self._close_quietly(rs=rs, stmt=stmt, conn=conn)

    @staticmethod
    def _resultset_to_dicts(rs) -> list[dict]:
        """
        Convert java.sql.ResultSet to Python list[dict] using column metadata.
        Args:
          - rs: java.sql.ResultSet positioned before the first row.
        Returns:
          - list[dict]: e.g.,
            [
              {"UniqueIdentifier": "2025-11-15_ABC123", "Title": "Order Report", ...},
              {"UniqueIdentifier": "2025-11-14_DEF456", "Title": "Order Report", ...}
            ]
        """
        meta = rs.getMetaData()
        cols = [meta.getColumnName(i) for i in range(1, meta.getColumnCount() + 1)]
        # Stream rows and build {column_name: value} dicts
        out: list[dict] = []
        while rs.next():
            out.append({cols[i]: rs.getString(i + 1) for i in range(len(cols))})
        return out


    def _close_quietly(self,
                       rs: Optional[Any] = None,
                       stmt: Optional[Any] = None,
                       conn: Optional[Any] = None) -> None:
        def _safe_close(obj: Optional[Any], name: str) -> None:
            if obj is None:
                return
            try:
                obj.close()
            except (self.SQLException, JException) as e:
                self.logger.debug("Ignored %s close error: %s", name, e)

        _safe_close(rs,   "ResultSet")
        _safe_close(stmt, "Statement")
        _safe_close(conn, "Connection")


    @staticmethod
    def shutdown():
        """
        Shutdown JVM safely — call this only once after all tests complete.
        DO NOT call during parallel test execution.
        """
        if jpype.isJVMStarted():
            try:
                jpype.shutdownJVM()
                print("JVM shutdown successfully.")
            except Exception as e:
                print("JVM shutdown warning:", e)

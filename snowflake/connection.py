"""
GeoPulse Snowflake Connection Manager
Handles secure authentication, session management, and connectivity diagnostics
for the GEOPULSE_DB data warehouse without exposing credentials.
"""
from typing import Optional, Dict, Any, Tuple
import os
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from config.settings import SNOWFLAKE_CONFIG


class SnowflakeConnectionManager:
    """Manages Snowflake connections, configuration validation, and connection testing."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or SNOWFLAKE_CONFIG
        self.account = self.config.get("account", "").strip()
        self.user = self.config.get("user", "").strip()
        self.password = self.config.get("password", "").strip()
        self.database = self.config.get("database", "GEOPULSE_DB").strip()
        self.warehouse = self.config.get("warehouse", "GEOPULSE_WH").strip()
        self.role = self.config.get("role", "ACCOUNTADMIN").strip()

    def has_credentials(self) -> bool:
        """Check if necessary Snowflake credentials have been provided."""
        placeholders = {"", "your_account_identifier", "your_account", "your_username", "your_password"}
        if self.account in placeholders:
            return False
        if self.user in placeholders:
            return False
        if self.password in placeholders:
            return False
        return True

    def get_connection(self):
        """Create and return a Snowflake connection object if credentials exist."""
        if not self.has_credentials():
            raise ConnectionError(
                "Snowflake credentials not configured in environment or .env file. "
                "Status: BLOCKED pending live Snowflake account."
            )

        try:
            import snowflake.connector
        except ImportError:
            raise ImportError(
                "snowflake-connector-python is not installed in the active environment."
            )

        conn = snowflake.connector.connect(
            account=self.account,
            user=self.user,
            password=self.password,
            database=self.database,
            warehouse=self.warehouse,
            role=self.role,
        )
        return conn

    def test_connection(self) -> Tuple[bool, str]:
        """Test Snowflake connectivity and return (is_connected, diagnostic_message)."""
        if not self.has_credentials():
            return (
                False,
                "BLOCKED: Snowflake account, user, or password not configured in .env. "
                "Local data preparation is intact and ready for upload upon credential availability.",
            )

        try:
            conn = self.get_connection()
            cur = conn.cursor()
            cur.execute("SELECT CURRENT_VERSION(), CURRENT_ACCOUNT(), CURRENT_WAREHOUSE()")
            row = cur.fetchone()
            cur.close()
            conn.close()
            return True, f"CONNECTED: Snowflake version {row[0]} on account {row[1]} (Warehouse: {row[2]})"
        except Exception as e:
            return False, f"CONNECTION_FAILED: {str(e)}"


def get_snowflake_connection():
    """Convenience factory function."""
    manager = SnowflakeConnectionManager()
    return manager.get_connection()


if __name__ == "__main__":
    mgr = SnowflakeConnectionManager()
    connected, msg = mgr.test_connection()
    print(f"[SnowflakeConnection] Status: {msg}")

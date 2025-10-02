import sqlite3
from datetime import datetime, date
from pathlib import Path
from typing import Optional, List, Dict, Any

class Database:
    def __init__(self, db_path: str = "timeclock.db"):
        self.db_path = Path(db_path)
        self.connection: Optional[sqlite3.Connection] = None
        self._init_database()

    def _init_database(self):
        """Initialize database with required tables."""
        self.connection = sqlite3.connect(self.db_path)
        self.connection.row_factory = sqlite3.Row
        cursor = self.connection.cursor()

        # Create sessions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                start_time TIMESTAMP NOT NULL,
                end_time TIMESTAMP,
                earnings REAL,
                memo TEXT
            )
        """)

        # Add memo column if it doesn't exist (for existing databases)
        try:
            cursor.execute("ALTER TABLE sessions ADD COLUMN memo TEXT")
            self.connection.commit()
        except sqlite3.OperationalError:
            # Column already exists
            pass

        # Create billing_cycles table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS billing_cycles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                start_date DATE NOT NULL,
                end_date DATE NOT NULL
            )
        """)

        # Create config table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS config (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """)

        # Set default config values if not exists
        cursor.execute("SELECT value FROM config WHERE key = 'hourly_rate'")
        if not cursor.fetchone():
            cursor.execute("INSERT INTO config (key, value) VALUES ('hourly_rate', '50.00')")

        self.connection.commit()

    def get_config(self, key: str) -> Optional[str]:
        """Get configuration value by key."""
        cursor = self.connection.cursor()
        cursor.execute("SELECT value FROM config WHERE key = ?", (key,))
        result = cursor.fetchone()
        return result['value'] if result else None

    def set_config(self, key: str, value: str):
        """Set configuration value."""
        cursor = self.connection.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO config (key, value)
            VALUES (?, ?)
        """, (key, value))
        self.connection.commit()

    def start_session(self) -> int:
        """Start a new work session."""
        cursor = self.connection.cursor()
        cursor.execute("""
            INSERT INTO sessions (start_time)
            VALUES (?)
        """, (datetime.now(),))
        self.connection.commit()
        return cursor.lastrowid

    def end_session(self, session_id: int, earnings: float, memo: str = ""):
        """End a work session and record earnings."""
        cursor = self.connection.cursor()
        cursor.execute("""
            UPDATE sessions
            SET end_time = ?, earnings = ?, memo = ?
            WHERE id = ?
        """, (datetime.now(), earnings, memo, session_id))
        self.connection.commit()

    def get_current_session(self) -> Optional[Dict[str, Any]]:
        """Get the current active session (no end_time)."""
        cursor = self.connection.cursor()
        cursor.execute("""
            SELECT id, start_time, end_time, earnings, memo
            FROM sessions
            WHERE end_time IS NULL
            ORDER BY start_time DESC
            LIMIT 1
        """)
        result = cursor.fetchone()
        if result:
            return dict(result)
        return None

    def get_current_billing_cycle(self) -> Optional[Dict[str, Any]]:
        """Get the current billing cycle."""
        cursor = self.connection.cursor()
        today = date.today()
        cursor.execute("""
            SELECT id, name, start_date, end_date
            FROM billing_cycles
            WHERE ? BETWEEN start_date AND end_date
            ORDER BY start_date DESC
            LIMIT 1
        """, (today,))
        result = cursor.fetchone()
        if result:
            return dict(result)
        return None

    def create_billing_cycle(self, name: str, start_date: date, end_date: date) -> int:
        """Create a new billing cycle."""
        cursor = self.connection.cursor()
        cursor.execute("""
            INSERT INTO billing_cycles (name, start_date, end_date)
            VALUES (?, ?, ?)
        """, (name, start_date, end_date))
        self.connection.commit()
        return cursor.lastrowid

    def get_billing_cycle_earnings(self, cycle_id: int) -> float:
        """Get total earnings for a billing cycle."""
        cursor = self.connection.cursor()
        cycle = cursor.execute("""
            SELECT start_date, end_date FROM billing_cycles WHERE id = ?
        """, (cycle_id,)).fetchone()

        if not cycle:
            return 0.0

        cursor.execute("""
            SELECT SUM(earnings) as total
            FROM sessions
            WHERE DATE(start_time) BETWEEN ? AND ?
            AND earnings IS NOT NULL
        """, (cycle['start_date'], cycle['end_date']))

        result = cursor.fetchone()
        return result['total'] if result and result['total'] else 0.0

    def get_all_billing_cycles(self) -> List[Dict[str, Any]]:
        """Get all billing cycles ordered by start date."""
        cursor = self.connection.cursor()
        cursor.execute("""
            SELECT id, name, start_date, end_date
            FROM billing_cycles
            ORDER BY start_date DESC
        """)
        return [dict(row) for row in cursor.fetchall()]

    def get_sessions_for_period(self, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """Get all sessions within a date range."""
        cursor = self.connection.cursor()
        cursor.execute("""
            SELECT id, start_time, end_time, earnings, memo
            FROM sessions
            WHERE DATE(start_time) BETWEEN ? AND ?
            ORDER BY start_time
        """, (start_date, end_date))
        return [dict(row) for row in cursor.fetchall()]

    def close(self):
        """Close database connection."""
        if self.connection:
            self.connection.close()
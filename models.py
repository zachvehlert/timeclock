from datetime import datetime, date, timedelta
from typing import Optional
from database import Database

class TimeClock:
    def __init__(self, db: Database):
        self.db = db
        self.current_session_id: Optional[int] = None
        self.hourly_rate = float(db.get_config('hourly_rate') or 50.0)
        self._load_current_session()
        self._ensure_billing_cycle()

    def _load_current_session(self):
        """Load any existing active session."""
        session = self.db.get_current_session()
        if session:
            self.current_session_id = session['id']

    def _ensure_billing_cycle(self):
        """Ensure there's a billing cycle for the current period."""
        cycle = self.db.get_current_billing_cycle()
        if not cycle:
            # Create a bi-weekly billing cycle (Friday to Thursday)
            today = date.today()

            # Find the most recent Friday (or today if it's Friday)
            # weekday(): Monday=0, Tuesday=1, ..., Friday=4, Saturday=5, Sunday=6
            days_since_friday = (today.weekday() - 4) % 7
            cycle_start = today - timedelta(days=days_since_friday)

            # Bi-weekly cycle ends 13 days after start (2 weeks minus 1 day)
            cycle_end = cycle_start + timedelta(days=13)

            cycle_name = f"Pay Period {cycle_start.strftime('%m/%d')} - {cycle_end.strftime('%m/%d')}"
            self.db.create_billing_cycle(cycle_name, cycle_start, cycle_end)

    def clock_in(self) -> datetime:
        """Clock in for a new session."""
        if self.current_session_id:
            # Already clocked in
            session = self.db.get_current_session()
            return datetime.fromisoformat(session['start_time'])

        self.current_session_id = self.db.start_session()
        return datetime.now()

    def clock_out(self) -> Optional[float]:
        """Clock out and calculate earnings."""
        if not self.current_session_id:
            return None

        session = self.db.get_current_session()
        if not session:
            return None

        start_time = datetime.fromisoformat(session['start_time'])
        duration = datetime.now() - start_time
        hours_worked = duration.total_seconds() / 3600
        earnings = hours_worked * self.hourly_rate

        self.db.end_session(self.current_session_id, earnings)
        self.current_session_id = None

        return earnings

    def get_session_info(self) -> Optional[dict]:
        """Get current session information."""
        if not self.current_session_id:
            return None

        session = self.db.get_current_session()
        if not session:
            return None

        start_time = datetime.fromisoformat(session['start_time'])
        duration = datetime.now() - start_time
        hours_worked = duration.total_seconds() / 3600
        current_earnings = hours_worked * self.hourly_rate

        return {
            'start_time': start_time,
            'duration': duration,
            'hours_worked': hours_worked,
            'current_earnings': current_earnings
        }

    def get_billing_cycle_earnings(self) -> float:
        """Get total earnings for current billing cycle including current session."""
        cycle = self.db.get_current_billing_cycle()
        if not cycle:
            return 0.0

        # Get saved earnings from completed sessions
        saved_earnings = self.db.get_billing_cycle_earnings(cycle['id'])

        # Add current session earnings if clocked in
        if self.current_session_id:
            session_info = self.get_session_info()
            if session_info:
                saved_earnings += session_info['current_earnings']

        return saved_earnings

    def set_hourly_rate(self, rate: float):
        """Update hourly rate."""
        self.hourly_rate = rate
        self.db.set_config('hourly_rate', str(rate))

    def is_clocked_in(self) -> bool:
        """Check if currently clocked in."""
        return self.current_session_id is not None
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.align import Align

class TimeclockUI:
    def __init__(self):
        self.console = Console()

    def create_progress_bar(self, elapsed_seconds: int) -> str:
        """Create a progress bar for the current hour since clock-in."""
        # Get minutes and seconds within current hour
        minutes = (elapsed_seconds % 3600) // 60
        seconds = elapsed_seconds % 60

        # Calculate progress through current hour (0-3600 seconds)
        hour_seconds = (elapsed_seconds % 3600)
        progress_percent = (hour_seconds / 3600) * 100

        # Create bar (20 characters wide)
        filled = int(progress_percent / 5)  # Each char represents 5%
        bar = '█' * filled + '░' * (20 - filled)

        return f"[{bar}] {minutes:02d}:{seconds:02d}/60:00"

    def create_display(self, session_info: dict = None, hourly_rate: float = 50.0,
                      cycle_earnings: float = 0.0) -> Panel:
        """Create the main display panel."""
        now = datetime.now()

        # Build the display content as a single string
        lines = []

        # Header
        lines.append("TIMECLOCK TERMINAL")
        lines.append("")

        # Progress bar (only show if clocked in)
        if session_info:
            elapsed_seconds = int(session_info['duration'].total_seconds())
            lines.append("Current Hour Progress:")
            lines.append(self.create_progress_bar(elapsed_seconds))
            lines.append("")

            start_time = session_info['start_time']
            current_earnings = session_info['current_earnings']

            lines.append(f"Clocked In: {start_time.strftime('%I:%M %p')}")
            lines.append(f"Hourly Rate: ${hourly_rate:.2f}")
            lines.append("")
            lines.append(f"Session Earnings: ${current_earnings:.2f}")
            lines.append(f"Pay Period Earnings: ${cycle_earnings:,.2f}")
        else:
            lines.append("Status: Not clocked in")
            lines.append(f"Hourly Rate: ${hourly_rate:.2f}")
            lines.append("")
            lines.append("Session Earnings: $0.00")
            lines.append(f"Pay Period Earnings: ${cycle_earnings:,.2f}")

        lines.append("")
        lines.append(f"Current Time: {now.strftime('%I:%M:%S %p')}")

        # Combine all lines into a single string
        content = "\n".join(lines)

        # Create panel with double-line border
        panel = Panel(
            Align.center(Text(content, justify="left")),
            border_style="bright_cyan",
            padding=(1, 2),
            expand=False,
            width=44,
            height=16
        )

        return panel
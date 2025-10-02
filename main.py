import time
import sys
import json
from datetime import datetime
from rich.live import Live
from rich.console import Console

from database import Database
from models import TimeClock
from ui import TimeclockUI


class TimeclockApp:
    def __init__(self):
        self.console = Console()
        self.load_config()
        self.db = Database(self.config.get('database_path', 'timeclock.db'))
        self.timeclock = TimeClock(self.db)
        self.ui = TimeclockUI()
        self.running = True

        # Set hourly rate from config
        if 'hourly_rate' in self.config:
            self.timeclock.set_hourly_rate(self.config['hourly_rate'])

        # Auto clock-in based on config
        if self.config.get('auto_clock_in', True) and not self.timeclock.is_clocked_in():
            self.timeclock.clock_in()
            self.console.print("[green]Auto clocked in![/green]")
            time.sleep(1)

    def load_config(self):
        """Load configuration from config.json."""
        try:
            with open('config.json', 'r') as f:
                self.config = json.load(f)
        except FileNotFoundError:
            self.console.print("[yellow]No config.json found, using defaults[/yellow]")
            self.config = {
                'hourly_rate': 50.00,
                'billing_cycle_type': 'monthly',
                'auto_clock_in': True,
                'auto_clock_out': True,
                'database_path': 'timeclock.db'
            }
            # Save default config
            with open('config.json', 'w') as f:
                json.dump(self.config, f, indent=2)
        except json.JSONDecodeError:
            self.console.print("[red]Error reading config.json, using defaults[/red]")
            self.config = {
                'hourly_rate': 50.00,
                'billing_cycle_type': 'monthly',
                'auto_clock_in': True,
                'auto_clock_out': True,
                'database_path': 'timeclock.db'
            }

    def run(self):
        """Main application loop."""
        try:
            with Live(refresh_per_second=1, screen=True) as live:
                while self.running:
                    # Update display
                    session_info = self.timeclock.get_session_info()
                    cycle_earnings = self.timeclock.get_billing_cycle_earnings()

                    # Create the display (without controls)
                    display = self.ui.create_display(
                        session_info=session_info,
                        hourly_rate=self.timeclock.hourly_rate,
                        cycle_earnings=cycle_earnings
                    )

                    # Update live display
                    live.update(display)

                    time.sleep(1)  # Update display every second

        except KeyboardInterrupt:
            pass
        finally:
            self.cleanup()

    def cleanup(self):
        """Clean up resources."""
        # Auto clock-out based on config
        if self.config.get('auto_clock_out', True) and self.timeclock.is_clocked_in():
            # Prompt for memo
            self.console.print("\n[cyan]Add a memo for this session (press Enter to skip):[/cyan]")
            try:
                memo = input("> ").strip()
            except (EOFError, KeyboardInterrupt):
                memo = ""

            earnings = self.timeclock.clock_out(memo)
            self.console.print(f"[yellow]Auto clocked out! Session earnings: ${earnings:.2f}[/yellow]")

        self.db.close()
        self.console.print("[dim]Goodbye![/dim]")


def main():
    app = TimeclockApp()
    app.run()


if __name__ == "__main__":
    main()

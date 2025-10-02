import csv
import json
from datetime import datetime
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.prompt import IntPrompt

from database import Database


class TimeclockExporter:
    def __init__(self):
        self.console = Console()
        self.load_config()
        self.db = Database(self.config.get('database_path', 'timeclock.db'))

    def load_config(self):
        """Load configuration from config.json."""
        try:
            with open('config.json', 'r') as f:
                self.config = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.config = {'database_path': 'timeclock.db'}

    def display_pay_periods(self):
        """Display all pay periods and let user select one."""
        periods = self.db.get_all_billing_cycles()

        if not periods:
            self.console.print("[red]No pay periods found in database.[/red]")
            return None

        # Create a table to display periods
        table = Table(title="Available Pay Periods")
        table.add_column("#", style="cyan", width=4)
        table.add_column("Pay Period", style="green")
        table.add_column("Start Date", style="yellow")
        table.add_column("End Date", style="yellow")

        for idx, period in enumerate(periods, 1):
            table.add_row(
                str(idx),
                period['name'],
                period['start_date'],
                period['end_date']
            )

        self.console.print(table)

        # Get user selection
        try:
            selection = IntPrompt.ask(
                "\nSelect pay period to export",
                choices=[str(i) for i in range(1, len(periods) + 1)]
            )
            return periods[selection - 1]
        except (KeyboardInterrupt, EOFError):
            self.console.print("\n[yellow]Export cancelled.[/yellow]")
            return None

    def export_to_csv(self, period):
        """Export sessions from selected period to CSV."""
        sessions = self.db.get_sessions_for_period(
            period['start_date'],
            period['end_date']
        )

        if not sessions:
            self.console.print(f"[yellow]No sessions found for {period['name']}[/yellow]")
            return

        # Generate filename
        start_date = period['start_date'].replace('-', '')
        end_date = period['end_date'].replace('-', '')
        filename = f"timeclock_export_{start_date}_{end_date}.csv"

        # Calculate totals
        total_hours = 0
        total_earnings = 0

        # Write to CSV
        with open(filename, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)

            # Write header
            writer.writerow([
                'Date',
                'Start Time',
                'End Time',
                'Duration (hours)',
                'Hourly Rate',
                'Earnings',
                'Memo'
            ])

            hourly_rate = self.config.get('hourly_rate', 50.00)

            for session in sessions:
                if session['start_time'] and session['end_time']:
                    start = datetime.fromisoformat(session['start_time'])
                    end = datetime.fromisoformat(session['end_time'])
                    duration = (end - start).total_seconds() / 3600  # hours

                    writer.writerow([
                        start.strftime('%Y-%m-%d'),
                        start.strftime('%I:%M %p'),
                        end.strftime('%I:%M %p'),
                        f"{duration:.2f}",
                        f"${hourly_rate:.2f}",
                        f"${session['earnings']:.2f}" if session['earnings'] else "$0.00",
                        session.get('memo', '') or ''
                    ])

                    total_hours += duration
                    if session['earnings']:
                        total_earnings += session['earnings']

            # Write totals
            writer.writerow([])  # Empty row
            writer.writerow(['', '', 'TOTAL:', f"{total_hours:.2f}", '', f"${total_earnings:.2f}"])

        self.console.print(f"\n[green]✓ Exported to {filename}[/green]")
        self.console.print(f"Total hours: {total_hours:.2f}")
        self.console.print(f"Total earnings: ${total_earnings:.2f}")

    def run(self):
        """Main export workflow."""
        self.console.print("[bold cyan]Timeclock Data Exporter[/bold cyan]\n")

        period = self.display_pay_periods()
        if period:
            self.console.print(f"\nExporting data for: [cyan]{period['name']}[/cyan]")
            self.export_to_csv(period)

        self.db.close()


def main():
    exporter = TimeclockExporter()
    exporter.run()


if __name__ == "__main__":
    main()
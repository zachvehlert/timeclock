# Timeclock Terminal

A simple, elegant terminal-based time tracking application for freelancers and hourly workers. Track your work sessions, monitor earnings in real-time, and export data for invoicing.

## Features

- **Real-time tracking**: Watch your earnings grow as you work
- **Automatic clock-in/out**: Configurable auto-start and auto-stop
- **Hourly progress bar**: Visual indicator that resets every hour of work
- **Bi-weekly pay periods**: Track earnings per pay period (Friday to Thursday)
- **CSV export**: Export any pay period's data for invoicing or records
- **Persistent storage**: SQLite database keeps all your time records safe
- **Clean terminal UI**: Minimalist design focused on the essential information

## Installation

This project uses `uv` for Python package management.

```bash
# Clone the repository
git clone <repository-url>
cd timeclock

# Install dependencies (uv will handle this automatically)
uv run python main.py
```

## Usage

### Running the Timeclock

Start the timeclock application:

```bash
uv run python main.py
```

The application will:
1. Auto clock you in (if configured)
2. Display a real-time dashboard showing:
   - Progress through current work hour
   - Clock-in time
   - Current session earnings
   - Total pay period earnings
   - Current time

Press `Ctrl+C` to exit. The app will auto clock you out (if configured).

### Exporting Data

Export timeclock data for any pay period to CSV:

```bash
uv run python export.py
```

This will:
1. Show you all available pay periods
2. Let you select which period to export
3. Create a CSV file with all sessions from that period
4. Include totals for hours worked and earnings

## Configuration

Edit `config.json` to customize your settings:

```json
{
  "hourly_rate": 45.00,
  "billing_cycle_type": "biweekly",
  "auto_clock_in": true,
  "auto_clock_out": true,
  "database_path": "timeclock.db"
}
```

### Configuration Options

- **hourly_rate**: Your hourly rate in dollars
- **billing_cycle_type**: Currently supports "biweekly" (Friday to Thursday)
- **auto_clock_in**: Automatically clock in when starting the app
- **auto_clock_out**: Automatically clock out when exiting the app
- **database_path**: Path to the SQLite database file

## Display Information

The terminal displays:

- **Current Hour Progress**: Shows progress through each 60-minute work hour
- **Clocked In**: When you started the current session
- **Session Earnings**: Real-time earnings for current session
- **Pay Period Earnings**: Total earnings for current pay period (updates live)

## Database

The application uses SQLite to store:
- Work sessions (start time, end time, earnings)
- Pay periods (bi-weekly, Friday to Thursday)
- Configuration settings

The database is created automatically on first run.

## Project Structure

timeclock/
main.py           # Main application with terminal UI
database.py       # SQLite database operations
models.py         # Business logic and time tracking
ui.py            # Terminal UI components using Rich
export.py        # CSV export functionality
config.json      # User configuration
timeclock.db     # SQLite database (auto-created)


## Dependencies

- **rich**: Terminal UI and formatting
- **sqlite3**: Database storage (built-in)
- **csv**: Data export (built-in)

## Tips

- The progress bar resets every hour of work time, not clock time
- Pay periods run Friday to Thursday
- All times are stored in your local timezone
- Export your data regularly for backup and invoicing
- Session earnings and pay period earnings update in real-time

## Troubleshooting

**Database Issues**: Delete `timeclock.db` to start fresh with a new database

**Config Issues**: Delete `config.json` to regenerate default configuration

**Display Issues**: Ensure your terminal is at least 80 characters wide

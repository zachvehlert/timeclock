#!/usr/bin/env python3

from datetime import datetime, date, time
from database import Database
from typing import Optional, List, Dict, Any
import sys
import os

class Colors:
    """ANSI color codes for terminal output."""
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'

    # Regular colors
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'

    # Bright colors
    BRIGHT_BLACK = '\033[90m'
    BRIGHT_RED = '\033[91m'
    BRIGHT_GREEN = '\033[92m'
    BRIGHT_YELLOW = '\033[93m'
    BRIGHT_BLUE = '\033[94m'
    BRIGHT_MAGENTA = '\033[95m'
    BRIGHT_CYAN = '\033[96m'
    BRIGHT_WHITE = '\033[97m'

    # Background colors
    BG_BLACK = '\033[40m'
    BG_RED = '\033[41m'
    BG_GREEN = '\033[42m'
    BG_YELLOW = '\033[43m'
    BG_BLUE = '\033[44m'
    BG_MAGENTA = '\033[45m'
    BG_CYAN = '\033[46m'
    BG_WHITE = '\033[47m'

class TimeclockEditor:
    def __init__(self):
        self.db = Database()
        self.hourly_rate = float(self.db.get_config('hourly_rate') or 50.0)

    def clear_screen(self):
        """Clear the terminal screen."""
        os.system('clear' if os.name == 'posix' else 'cls')

    def run(self):
        """Main interactive loop."""
        while True:
            self.clear_screen()
            self.show_pay_periods()
            choice = input(f"\n{Colors.BRIGHT_CYAN}Enter pay period number (or 'q' to quit): {Colors.RESET}").strip()

            if choice.lower() == 'q':
                break

            try:
                period_index = int(choice) - 1
                pay_periods = self.db.get_all_billing_cycles()
                if 0 <= period_index < len(pay_periods):
                    self.show_days_in_period(pay_periods[period_index])
                else:
                    print(f"{Colors.RED}Invalid pay period number.{Colors.RESET}")
                    input(f"{Colors.DIM}Press Enter to continue...{Colors.RESET}")
            except ValueError:
                print(f"{Colors.RED}Please enter a valid number or 'q' to quit.{Colors.RESET}")
                input(f"{Colors.DIM}Press Enter to continue...{Colors.RESET}")

    def show_pay_periods(self):
        """Display all pay periods."""
        print(f"{Colors.BRIGHT_BLUE}{'='*50}")
        print(f"{Colors.BOLD}{Colors.BRIGHT_WHITE}PAY PERIODS{Colors.RESET}")
        print(f"{Colors.BRIGHT_BLUE}{'='*50}{Colors.RESET}")

        pay_periods = self.db.get_all_billing_cycles()
        if not pay_periods:
            print(f"{Colors.YELLOW}No pay periods found.{Colors.RESET}")
            return

        for i, period in enumerate(pay_periods, 1):
            start_date = period['start_date']
            end_date = period['end_date']
            earnings = self.db.get_billing_cycle_earnings(period['id'])

            # Color earnings based on amount
            earnings_color = Colors.BRIGHT_GREEN if earnings > 0 else Colors.BRIGHT_BLACK

            print(f"{Colors.BRIGHT_CYAN}{i}.{Colors.RESET} {Colors.WHITE}{period['name']}{Colors.RESET} "
                  f"{Colors.BRIGHT_BLACK}({start_date} to {end_date}){Colors.RESET} - "
                  f"{earnings_color}${earnings:.2f}{Colors.RESET}")

    def show_days_in_period(self, period: Dict[str, Any]):
        """Display days with sessions in the selected pay period."""
        while True:
            self.clear_screen()
            print(f"{Colors.BRIGHT_MAGENTA}{'='*50}")
            print(f"{Colors.BOLD}{Colors.BRIGHT_WHITE}DAYS IN {period['name']}{Colors.RESET}")
            print(f"{Colors.BRIGHT_MAGENTA}{'='*50}{Colors.RESET}")

            sessions = self.db.get_sessions_for_period(period['start_date'], period['end_date'])

            # Group sessions by date
            days = {}
            for session in sessions:
                session_date = datetime.fromisoformat(session['start_time']).date()
                if session_date not in days:
                    days[session_date] = []
                days[session_date].append(session)

            if not days:
                print(f"{Colors.YELLOW}No sessions found in this pay period.{Colors.RESET}")
                input(f"\n{Colors.DIM}Press Enter to return to pay periods...{Colors.RESET}")
                return

            # Display days
            sorted_days = sorted(days.keys())
            for i, day in enumerate(sorted_days, 1):
                day_sessions = days[day]
                total_earnings = sum(s['earnings'] or 0 for s in day_sessions)
                session_count = len(day_sessions)

                # Color earnings and format day
                earnings_color = Colors.BRIGHT_GREEN if total_earnings > 0 else Colors.BRIGHT_BLACK
                day_color = Colors.BRIGHT_CYAN

                print(f"{day_color}{i}.{Colors.RESET} {Colors.WHITE}{day}{Colors.RESET} - "
                      f"{Colors.BRIGHT_YELLOW}{session_count} session(s){Colors.RESET} - "
                      f"{earnings_color}${total_earnings:.2f}{Colors.RESET}")

            print(f"{Colors.BRIGHT_GREEN}{len(sorted_days) + 1}. Add new session{Colors.RESET}")

            choice = input(f"\n{Colors.BRIGHT_CYAN}Enter day number, 'n' for new session, or 'b' to go back: {Colors.RESET}").strip()

            if choice.lower() == 'b':
                return
            elif choice.lower() == 'n':
                self.create_new_session(period)
            else:
                try:
                    day_index = int(choice) - 1
                    if 0 <= day_index < len(sorted_days):
                        selected_day = sorted_days[day_index]
                        self.show_entries_for_day(selected_day, days[selected_day], period)
                    else:
                        print(f"{Colors.RED}Invalid day number.{Colors.RESET}")
                        input(f"{Colors.DIM}Press Enter to continue...{Colors.RESET}")
                except ValueError:
                    print(f"{Colors.RED}Please enter a valid number, 'n', or 'b'.{Colors.RESET}")
                    input(f"{Colors.DIM}Press Enter to continue...{Colors.RESET}")

    def show_entries_for_day(self, day: date, sessions: List[Dict[str, Any]], period: Dict[str, Any]):
        """Display entries for a specific day."""
        while True:
            self.clear_screen()
            print(f"{Colors.BRIGHT_YELLOW}{'='*50}")
            print(f"{Colors.BOLD}{Colors.BRIGHT_WHITE}ENTRIES FOR {day}{Colors.RESET}")
            print(f"{Colors.BRIGHT_YELLOW}{'='*50}{Colors.RESET}")

            for i, session in enumerate(sessions, 1):
                start_time = datetime.fromisoformat(session['start_time'])
                end_time = datetime.fromisoformat(session['end_time']) if session['end_time'] else None
                earnings = session['earnings'] or 0

                status = "ACTIVE" if not end_time else "COMPLETED"
                end_str = end_time.strftime("%H:%M:%S") if end_time else "ACTIVE"

                # Color coding based on status
                status_color = Colors.BRIGHT_RED if status == "ACTIVE" else Colors.BRIGHT_GREEN
                earnings_color = Colors.BRIGHT_GREEN if earnings > 0 else Colors.BRIGHT_BLACK
                time_color = Colors.BRIGHT_WHITE

                print(f"{Colors.BRIGHT_CYAN}{i}.{Colors.RESET} {time_color}{start_time.strftime('%H:%M:%S')}{Colors.RESET} - "
                      f"{time_color}{end_str}{Colors.RESET} "
                      f"({earnings_color}${earnings:.2f}{Colors.RESET}) "
                      f"[{status_color}{status}{Colors.RESET}]")

            print(f"{Colors.BRIGHT_GREEN}{len(sessions) + 1}. Add new entry{Colors.RESET}")

            choice = input(f"\n{Colors.BRIGHT_CYAN}Select entry (1-{len(sessions)}), 'n' for new entry, or 'b' to go back: {Colors.RESET}").strip()

            if choice.lower() == 'b':
                return
            elif choice.lower() == 'n':
                self.create_new_session(period, day)
            else:
                try:
                    entry_index = int(choice) - 1
                    if 0 <= entry_index < len(sessions):
                        self.edit_session(sessions[entry_index], period)
                        # Refresh sessions list
                        sessions = [s for s in self.db.get_sessions_for_period(period['start_date'], period['end_date'])
                                  if datetime.fromisoformat(s['start_time']).date() == day]
                    else:
                        print(f"{Colors.RED}Invalid entry number.{Colors.RESET}")
                        input(f"{Colors.DIM}Press Enter to continue...{Colors.RESET}")
                except ValueError:
                    print(f"{Colors.RED}Please enter a valid number, 'n', or 'b'.{Colors.RESET}")
                    input(f"{Colors.DIM}Press Enter to continue...{Colors.RESET}")

    def edit_session(self, session: Dict[str, Any], period: Dict[str, Any]):
        """Edit or delete a session."""
        while True:
            self.clear_screen()
            start_time = datetime.fromisoformat(session['start_time'])
            end_time = datetime.fromisoformat(session['end_time']) if session['end_time'] else None
            earnings = session['earnings'] or 0

            print(f"{Colors.BRIGHT_RED}{'='*50}")
            print(f"{Colors.BOLD}{Colors.BRIGHT_WHITE}EDIT SESSION {session['id']}{Colors.RESET}")
            print(f"{Colors.BRIGHT_RED}{'='*50}{Colors.RESET}")
            print(f"{Colors.BRIGHT_YELLOW}Start Time:{Colors.RESET} {Colors.WHITE}{start_time.strftime('%Y-%m-%d %H:%M:%S')}{Colors.RESET}")
            print(f"{Colors.BRIGHT_YELLOW}End Time:{Colors.RESET} {Colors.WHITE}{end_time.strftime('%Y-%m-%d %H:%M:%S') if end_time else 'ACTIVE'}{Colors.RESET}")
            print(f"{Colors.BRIGHT_YELLOW}Earnings:{Colors.RESET} {Colors.BRIGHT_GREEN}${earnings:.2f}{Colors.RESET}")

            print(f"\n{Colors.BRIGHT_CYAN}Options:{Colors.RESET}")
            print(f"{Colors.BRIGHT_CYAN}1.{Colors.RESET} Edit start time")
            print(f"{Colors.BRIGHT_CYAN}2.{Colors.RESET} Edit end time")
            print(f"{Colors.BRIGHT_CYAN}3.{Colors.RESET} Edit earnings")
            print(f"{Colors.BRIGHT_RED}4.{Colors.RESET} Delete session")
            print(f"{Colors.BRIGHT_CYAN}5.{Colors.RESET} Back to entries")

            choice = input(f"{Colors.BRIGHT_CYAN}Select option: {Colors.RESET}").strip()

            if choice == '1':
                self.edit_start_time(session)
                return
            elif choice == '2':
                self.edit_end_time(session)
                return
            elif choice == '3':
                self.edit_earnings(session)
                return
            elif choice == '4':
                if self.confirm_delete():
                    self.delete_session(session)
                return
            elif choice == '5':
                return
            else:
                print(f"{Colors.RED}Invalid option. Please try again.{Colors.RESET}")
                input(f"{Colors.DIM}Press Enter to continue...{Colors.RESET}")

    def edit_start_time(self, session: Dict[str, Any]):
        """Edit session start time and recalculate earnings."""
        current_start = datetime.fromisoformat(session['start_time'])
        print(f"\n{Colors.BRIGHT_YELLOW}Current start time:{Colors.RESET} {Colors.WHITE}{current_start.strftime('%Y-%m-%d %H:%M:%S')}{Colors.RESET}")

        new_time_str = input(f"{Colors.BRIGHT_CYAN}Enter new start time (YYYY-MM-DD HH:MM:SS): {Colors.RESET}").strip()
        try:
            new_start_time = datetime.strptime(new_time_str, '%Y-%m-%d %H:%M:%S')

            # Recalculate earnings if session has end time
            new_earnings = session['earnings']
            if session['end_time']:
                end_time = datetime.fromisoformat(session['end_time'])
                duration = end_time - new_start_time
                hours_worked = duration.total_seconds() / 3600
                new_earnings = hours_worked * self.hourly_rate

            cursor = self.db.connection.cursor()
            cursor.execute("UPDATE sessions SET start_time = ?, earnings = ? WHERE id = ?",
                          (new_start_time, new_earnings, session['id']))
            self.db.connection.commit()

            if session['end_time']:
                print(f"{Colors.BRIGHT_GREEN}Start time updated and earnings recalculated to ${new_earnings:.2f}!{Colors.RESET}")
            else:
                print(f"{Colors.BRIGHT_GREEN}Start time updated successfully!{Colors.RESET}")
            input(f"{Colors.DIM}Press Enter to continue...{Colors.RESET}")

        except ValueError:
            print(f"{Colors.RED}Invalid date format. Please use YYYY-MM-DD HH:MM:SS{Colors.RESET}")
            input(f"{Colors.DIM}Press Enter to continue...{Colors.RESET}")

    def edit_end_time(self, session: Dict[str, Any]):
        """Edit session end time and recalculate earnings."""
        current_end = session['end_time']
        print(f"\n{Colors.BRIGHT_YELLOW}Current end time:{Colors.RESET} {Colors.WHITE}{datetime.fromisoformat(current_end).strftime('%Y-%m-%d %H:%M:%S') if current_end else 'ACTIVE'}{Colors.RESET}")

        new_time_str = input(f"{Colors.BRIGHT_CYAN}Enter new end time (YYYY-MM-DD HH:MM:SS) or 'null' for active: {Colors.RESET}").strip()

        try:
            if new_time_str.lower() == 'null':
                new_end_time = None
                new_earnings = 0.0  # Active sessions have no earnings yet
            else:
                new_end_time = datetime.strptime(new_time_str, '%Y-%m-%d %H:%M:%S')
                # Recalculate earnings based on duration
                start_time = datetime.fromisoformat(session['start_time'])
                duration = new_end_time - start_time
                hours_worked = duration.total_seconds() / 3600
                new_earnings = hours_worked * self.hourly_rate

            cursor = self.db.connection.cursor()
            cursor.execute("UPDATE sessions SET end_time = ?, earnings = ? WHERE id = ?",
                          (new_end_time, new_earnings, session['id']))
            self.db.connection.commit()

            if new_end_time:
                print(f"{Colors.BRIGHT_GREEN}End time updated and earnings recalculated to ${new_earnings:.2f}!{Colors.RESET}")
            else:
                print(f"{Colors.BRIGHT_GREEN}End time cleared - session is now active!{Colors.RESET}")
            input(f"{Colors.DIM}Press Enter to continue...{Colors.RESET}")

        except ValueError:
            print(f"{Colors.RED}Invalid date format. Please use YYYY-MM-DD HH:MM:SS or 'null'{Colors.RESET}")
            input(f"{Colors.DIM}Press Enter to continue...{Colors.RESET}")

    def edit_earnings(self, session: Dict[str, Any]):
        """Edit session earnings."""
        current_earnings = session['earnings'] or 0
        print(f"\n{Colors.BRIGHT_YELLOW}Current earnings:{Colors.RESET} {Colors.BRIGHT_GREEN}${current_earnings:.2f}{Colors.RESET}")

        new_earnings_str = input(f"{Colors.BRIGHT_CYAN}Enter new earnings amount: {Colors.BRIGHT_GREEN}${Colors.RESET}").strip()
        try:
            new_earnings = float(new_earnings_str)

            cursor = self.db.connection.cursor()
            cursor.execute("UPDATE sessions SET earnings = ? WHERE id = ?",
                          (new_earnings, session['id']))
            self.db.connection.commit()

            print(f"{Colors.BRIGHT_GREEN}Earnings updated successfully!{Colors.RESET}")
            input(f"{Colors.DIM}Press Enter to continue...{Colors.RESET}")

        except ValueError:
            print(f"{Colors.RED}Invalid amount. Please enter a valid number.{Colors.RESET}")
            input(f"{Colors.DIM}Press Enter to continue...{Colors.RESET}")

    def delete_session(self, session: Dict[str, Any]):
        """Delete a session."""
        cursor = self.db.connection.cursor()
        cursor.execute("DELETE FROM sessions WHERE id = ?", (session['id'],))
        self.db.connection.commit()
        print(f"{Colors.BRIGHT_GREEN}Session deleted successfully!{Colors.RESET}")
        input(f"{Colors.DIM}Press Enter to continue...{Colors.RESET}")

    def confirm_delete(self) -> bool:
        """Confirm deletion action."""
        confirm = input(f"{Colors.BRIGHT_RED}Are you sure you want to delete this session? (y/N): {Colors.RESET}").strip().lower()
        return confirm == 'y'

    def create_new_session(self, period: Dict[str, Any], specific_date: Optional[date] = None):
        """Create a new session."""
        self.clear_screen()
        print(f"{Colors.BRIGHT_GREEN}{'='*50}")
        print(f"{Colors.BOLD}{Colors.BRIGHT_WHITE}CREATE NEW SESSION{Colors.RESET}")
        print(f"{Colors.BRIGHT_GREEN}{'='*50}{Colors.RESET}")

        # Get date
        if specific_date:
            session_date = specific_date
            print(f"{Colors.BRIGHT_YELLOW}Date:{Colors.RESET} {Colors.WHITE}{session_date}{Colors.RESET}")
        else:
            date_str = input(f"{Colors.BRIGHT_CYAN}Enter date (YYYY-MM-DD) or press Enter for today: {Colors.RESET}").strip()
            if not date_str:
                session_date = date.today()
            else:
                try:
                    session_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                except ValueError:
                    print(f"{Colors.RED}Invalid date format.{Colors.RESET}")
                    input(f"{Colors.DIM}Press Enter to continue...{Colors.RESET}")
                    return

        # Get start time
        start_time_str = input(f"{Colors.BRIGHT_CYAN}Enter start time (HH:MM:SS): {Colors.RESET}").strip()
        try:
            start_time_obj = datetime.strptime(start_time_str, '%H:%M:%S').time()
            start_datetime = datetime.combine(session_date, start_time_obj)
        except ValueError:
            print(f"{Colors.RED}Invalid time format. Please use HH:MM:SS{Colors.RESET}")
            input(f"{Colors.DIM}Press Enter to continue...{Colors.RESET}")
            return

        # Get end time
        end_time_str = input(f"{Colors.BRIGHT_CYAN}Enter end time (HH:MM:SS) or press Enter for active session: {Colors.RESET}").strip()
        end_datetime = None
        if end_time_str:
            try:
                end_time_obj = datetime.strptime(end_time_str, '%H:%M:%S').time()
                end_datetime = datetime.combine(session_date, end_time_obj)
            except ValueError:
                print(f"{Colors.RED}Invalid time format. Please use HH:MM:SS{Colors.RESET}")
                input(f"{Colors.DIM}Press Enter to continue...{Colors.RESET}")
                return

        # Get earnings
        earnings_str = input(f"{Colors.BRIGHT_CYAN}Enter earnings amount (or press Enter for 0): {Colors.BRIGHT_GREEN}${Colors.RESET}").strip()
        earnings = 0.0
        if earnings_str:
            try:
                earnings = float(earnings_str)
            except ValueError:
                print(f"{Colors.YELLOW}Invalid amount. Setting to $0.00{Colors.RESET}")
                earnings = 0.0

        # Create the session
        cursor = self.db.connection.cursor()
        cursor.execute("""
            INSERT INTO sessions (start_time, end_time, earnings)
            VALUES (?, ?, ?)
        """, (start_datetime, end_datetime, earnings))
        self.db.connection.commit()

        print(f"{Colors.BRIGHT_GREEN}New session created successfully!{Colors.RESET}")
        input(f"{Colors.DIM}Press Enter to continue...{Colors.RESET}")

def main():
    print(f"{Colors.BOLD}{Colors.BRIGHT_CYAN}{'='*60}")
    print(f"{Colors.BRIGHT_WHITE}🕐 TIMECLOCK DATABASE EDITOR 🕐{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BRIGHT_CYAN}{'='*60}{Colors.RESET}")
    print(f"{Colors.DIM}Navigate through pay periods → days → entries{Colors.RESET}")
    print(f"{Colors.DIM}Edit times, earnings, create/delete sessions{Colors.RESET}")

    editor = TimeclockEditor()
    try:
        editor.run()
    except KeyboardInterrupt:
        print(f"\n{Colors.BRIGHT_YELLOW}👋 Goodbye!{Colors.RESET}")
    finally:
        editor.db.close()

if __name__ == "__main__":
    main()
"""
Logger module - all output goes through here.
Writes to both terminal (colored) and a log file simultaneously.
"""

import logging
import sys
from datetime import datetime
from pathlib import Path


class Colors:
    RESET   = "\033[0m"
    BOLD    = "\033[1m"
    RED     = "\033[91m"
    GREEN   = "\033[92m"
    YELLOW  = "\033[93m"
    BLUE    = "\033[94m"
    CYAN    = "\033[96m"
    WHITE   = "\033[97m"
    DIM     = "\033[2m"


class SetupLogger:
    def __init__(self, log_file: str = "logs/setup.log"):
        self.log_path = Path(log_file)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

        self._file_logger = logging.getLogger("parrot_setup")
        self._file_logger.setLevel(logging.DEBUG)

        if not self._file_logger.handlers:
            fh = logging.FileHandler(self.log_path, encoding="utf-8")
            fh.setLevel(logging.DEBUG)
            fh.setFormatter(logging.Formatter(
                "%(asctime)s [%(levelname)s] %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S"
            ))
            self._file_logger.addHandler(fh)

    # ── public API ──────────────────────────────────────────────────────────

    def banner(self, text: str):
        line = "─" * 60
        print(f"\n{Colors.CYAN}{Colors.BOLD}{line}")
        print(f"  {text}")
        print(f"{line}{Colors.RESET}\n")
        self._file_logger.info(f"=== {text} ===")

    def section(self, text: str):
        print(f"\n{Colors.BLUE}{Colors.BOLD}▶  {text}{Colors.RESET}")
        self._file_logger.info(f"--- {text} ---")

    def info(self, text: str):
        print(f"  {Colors.WHITE}{text}{Colors.RESET}")
        self._file_logger.info(text)

    def success(self, text: str):
        print(f"  {Colors.GREEN}✔  {text}{Colors.RESET}")
        self._file_logger.info(f"SUCCESS: {text}")

    def warning(self, text: str):
        print(f"  {Colors.YELLOW}⚠  {text}{Colors.RESET}")
        self._file_logger.warning(text)

    def error(self, text: str):
        print(f"  {Colors.RED}✘  {text}{Colors.RESET}", file=sys.stderr)
        self._file_logger.error(text)

    def skip(self, text: str):
        print(f"  {Colors.DIM}–  {text} (skipped){Colors.RESET}")
        self._file_logger.debug(f"SKIPPED: {text}")

    def step(self, text: str):
        print(f"  {Colors.CYAN}→  {text}{Colors.RESET}")
        self._file_logger.debug(text)

    def result_summary(self, results: dict):
        """Print a clean install summary table."""
        ok      = results.get("success", [])
        failed  = results.get("failed", [])
        skipped = results.get("skipped", [])

        print(f"\n{Colors.BOLD}{'─'*60}{Colors.RESET}")
        print(f"  {Colors.GREEN}✔ Installed : {len(ok)}{Colors.RESET}")
        print(f"  {Colors.YELLOW}– Skipped   : {len(skipped)}{Colors.RESET}")
        print(f"  {Colors.RED}✘ Failed    : {len(failed)}{Colors.RESET}")
        print(f"  {Colors.DIM}Log saved   : {self.log_path}{Colors.RESET}")
        print(f"{Colors.BOLD}{'─'*60}{Colors.RESET}\n")

        if failed:
            print(f"  {Colors.RED}Failed items:{Colors.RESET}")
            for item in failed:
                print(f"    {Colors.RED}• {item}{Colors.RESET}")
            self._file_logger.error(f"Failed items: {failed}")

"""
Runner module - executes shell commands safely.
- Streams output in real time (so you see what apt is doing)
- Captures stderr for logging
- Returns success/failure cleanly
"""

import subprocess
import shutil
from typing import Optional
from modules.logger import SetupLogger


class Runner:
    def __init__(self, logger: SetupLogger, dry_run: bool = False):
        self.log     = logger
        self.dry_run = dry_run

    def run(
        self,
        cmd: list[str],
        label: str = "",
        capture: bool = False,
        env: Optional[dict] = None,
    ) -> bool:
        """
        Run a command.
        - dry_run=True  → just print, don't execute
        - capture=False → stream output live to terminal
        - capture=True  → suppress output, only log errors
        Returns True on success, False on failure.
        """
        display = label or " ".join(cmd)

        if self.dry_run:
            self.log.step(f"[DRY RUN] {' '.join(cmd)}")
            return True

        self.log.step(display)

        try:
            if capture:
                result = subprocess.run(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    env=env,
                )
                if result.returncode != 0:
                    self.log.error(f"{display} → {result.stderr.strip()}")
                    return False
            else:
                result = subprocess.run(cmd, text=True, env=env)
                if result.returncode != 0:
                    self.log.error(f"{display} failed (exit {result.returncode})")
                    return False

            return True

        except FileNotFoundError:
            self.log.error(f"Command not found: {cmd[0]}")
            return False
        except Exception as exc:
            self.log.error(f"{display} raised exception: {exc}")
            return False

    def binary_exists(self, name: str) -> bool:
        """Check if a binary is already on PATH."""
        return shutil.which(name) is not None

    def apt_installed(self, package: str) -> bool:
        """Check if an apt package is already installed."""
        result = subprocess.run(
            ["dpkg", "-s", package],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        return result.returncode == 0

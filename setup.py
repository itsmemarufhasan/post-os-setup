#!/usr/bin/env python3
"""
Parrot OS Post-Install Setup Tool
──────────────────────────────────
Author : rradhasan
Usage  : python3 setup.py [--dry-run] [--config path/to/tools.yaml]
"""

import argparse
import sys
from pathlib import Path

import yaml

from modules.logger     import SetupLogger
from modules.runner     import Runner
from modules.tui        import select_modules, confirm_run, dry_run_prompt
from modules.installers import (
    AptInstaller,
    DebInstaller,
    GoInstaller,
    ShellInstaller,
    GitHubInstaller,
    GoEnvInstaller,
    ExtrasInstaller,
    VirtualBoxInstaller,
    DockerInstaller,
    PipInstaller,
)


# ── helpers ──────────────────────────────────────────────────────────────────

def load_config(path: str) -> dict:
    config_path = Path(path)
    if not config_path.exists():
        print(f"[ERROR] Config file not found: {path}")
        sys.exit(1)
    with config_path.open("r") as f:
        return yaml.safe_load(f)


def merge_results(total: dict, new: dict):
    for key in ("success", "failed", "skipped"):
        total[key].extend(new.get(key, []))


# ── main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Parrot OS Post-Install Setup Tool"
    )
    parser.add_argument(
        "--config",
        default="config/tools.yaml",
        help="Path to YAML config file (default: config/tools.yaml)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show all commands without executing them",
    )
    args = parser.parse_args()

    # ── load config ──────────────────────────────────────────────────────────
    config   = load_config(args.config)
    meta     = config.get("meta", {})
    username = meta.get("username", "user")
    log_file = meta.get("log_file", "logs/setup.log")

    # ── TUI ──────────────────────────────────────────────────────────────────
    selected = select_modules()

    dry_run = args.dry_run or dry_run_prompt()

    if not confirm_run(selected):
        print("\n [-] Aborted.\n")
        sys.exit(0)

    # ── init core objects ─────────────────────────────────────────────────────
    log     = SetupLogger(log_file)
    runner  = Runner(log, dry_run=dry_run)

    apt_installer    = AptInstaller(runner, log)
    deb_installer    = DebInstaller(runner, log, deb_dir=meta.get("deb_dir", "deb"))
    go_installer     = GoInstaller(runner, log)
    shell_installer  = ShellInstaller(runner, log, username=username)
    github_installer = GitHubInstaller(runner, log)
    goenv_installer  = GoEnvInstaller(runner, log)
    extras_installer = ExtrasInstaller(runner, log)
    vbox_installer   = VirtualBoxInstaller(runner, log)
    docker_installer = DockerInstaller(runner, log, username=username)
    pip_installer = PipInstaller(runner, log)

    total_results = {"success": [], "failed": [], "skipped": []}

    log.banner("Parrot OS Setup — Starting")

    # ── SYSTEM UPDATE ─────────────────────────────────────────────────────────
    if "system" in selected:
        sys_cfg = config.get("system", {})
        if sys_cfg.get("update_before_install", True):
            apt_installer.update()

    # ── APT ──────────────────────────────────────────────────────────────────
    if "apt" in selected:
        log.banner("APT Tools Installation")
        for group in config.get("apt", []):
            res = apt_installer.install_category(
                group["category"],
                group["tools"],
            )
            merge_results(total_results, res)

        sys_cfg = config.get("system", {})
        if sys_cfg.get("fix_broken_after_install", True):
            apt_installer.fix_broken()
        if sys_cfg.get("autoremove_after_install", True):
            apt_installer.autoremove()

    # ── DEB ──────────────────────────────────────────────────────────────────
    if "deb" in selected:
        log.banner("DEB Package Installation")
        for group in config.get("deb", []):
            res = deb_installer.install_category(
                group["category"],
                group["packages"],
            )
            merge_results(total_results, res)

    # ── GO ENV ────────────────────────────────────────────────────────────────
    if "go_env" in selected:
        log.banner("Go Environment Configuration")
        goenv_cfg = config.get("go_env", {})
        res = goenv_installer.configure(goenv_cfg)
        merge_results(total_results, res)

    # ── GO ───────────────────────────────────────────────────────────────────
    if "go" in selected:
        log.banner("Go Tools Installation")
        if go_installer.check_go():
            for group in config.get("go", []):
                res = go_installer.install_category(
                    group["category"],
                    group["tools"],
                )
                merge_results(total_results, res)
        else:
            log.error("Skipping Go tools — Go not found.")

    # ── GITHUB TOOLS ──────────────────────────────────────────────────────────
    if "github" in selected:
        log.banner("GitHub Tools Setup")
        gh_cfg = config.get("github", {})
        res = github_installer.move_tools(
            source_dir=gh_cfg.get("source_dir", "tools"),
            dest_dir=gh_cfg.get("dest_dir", "/opt"),
        )
        merge_results(total_results, res)

    # ── SHELL ─────────────────────────────────────────────────────────────────
    if "shell" in selected:
        log.banner("Shell Configuration")
        shell_cfg = config.get("shell", {})
        res = shell_installer.install(shell_cfg)
        merge_results(total_results, res)

    # ── VIRTUALBOX ────────────────────────────────────────────────────────────
    if "virtualbox" in selected:
        log.banner("VirtualBox Repository & Install")
        vbox_cfg = config.get("virtualbox", {})
        res = vbox_installer.install(vbox_cfg)
        merge_results(total_results, res)

    # ── DOCKER ────────────────────────────────────────────────────────────────
    if "docker" in selected:
        log.banner("Docker CE Installation")
        docker_cfg = config.get("docker", {})
        res = docker_installer.install(docker_cfg)
        merge_results(total_results, res)

    # ── EXTRAS ────────────────────────────────────────────────────────────────
    if "extras" in selected:
        log.banner("Extras Installation")
        extras_cfg = config.get("extras", {})
        res = extras_installer.install(extras_cfg)
        merge_results(total_results, res)

    # ── PIP ──────────────────────────────────────────────────────────────────
    if "pip" in selected:
        log.banner("Pip Packages Installation")
        for group in config.get("pip", []):
            res = pip_installer.install_category(
                group["category"],
                group["tools"],
            )
            merge_results(total_results, res)

    # ── FINAL SUMMARY ────────────────────────────────────────────────────────
    log.banner("Setup Complete")
    log.result_summary(total_results)


if __name__ == "__main__":
    main()

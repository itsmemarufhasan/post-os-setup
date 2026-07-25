"""
TUI module - terminal user interface for selecting install modules.
Pure stdlib, no curses complexity. Clean and readable.
"""

import sys
from modules.logger import Colors


def clear():
    print("\033[2J\033[H", end="")


def print_banner():
    banner = r"""
  ██████╗  █████╗ ██████╗ ██████╗  ██████╗ ████████╗    ███████╗███████╗████████╗██╗   ██╗██████╗
  ██╔══██╗██╔══██╗██╔══██╗██╔══██╗██╔═══██╗╚══██╔══╝    ██╔════╝██╔════╝╚══██╔══╝██║   ██║██╔══██╗
  ██████╔╝███████║██████╔╝██████╔╝██║   ██║   ██║       ███████╗█████╗     ██║   ██║   ██║██████╔╝
  ██╔═══╝ ██╔══██║██╔══██╗██╔══██╗██║   ██║   ██║       ╚════██║██╔══╝     ██║   ██║   ██║██╔═══╝
  ██║     ██║  ██║██║  ██║██║  ██║╚██████╔╝   ██║       ███████║███████╗   ██║   ╚██████╔╝██║
  ╚═╝     ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝   ╚═╝       ╚══════╝╚══════╝   ╚═╝    ╚═════╝ ╚═╝
    """
    print(f"{Colors.CYAN}{Colors.BOLD}{banner}{Colors.RESET}")
    print(f"  {Colors.DIM}Parrot OS Post-Install Setup Tool  |  github.com/rradhasan{Colors.RESET}\n")


MODULES = [
    {
        "id":    "system",
        "label": "System Update",
        "desc":  "apt update before installing anything",
        "icon":  "🔄",
    },
    {
        "id":    "apt",
        "label": "APT Tools",
        "desc":  "Recon, web fuzzing, exploitation, dev tools, desktop apps",
        "icon":  "📦",
    },
    {
        "id":    "deb",
        "label": "DEB Packages",
        "desc":  "Chrome, VSCode, Discord, Nessus, VirtualBox, etc.",
        "icon":  "📥",
    },
    {
        "id":    "go",
        "label": "Go Tools",
        "desc":  "ProjectDiscovery suite, TomNomNom, Hakluke, and 80+ more",
        "icon":  "🐹",
    },
    {
        "id":    "github",
        "label": "GitHub Tools",
        "desc":  "Move pre-cloned tools from tools/ → /opt/",
        "icon":  "🐙",
    },
    {
        "id":    "shell",
        "label": "Shell Setup",
        "desc":  "Copy dotfiles, change shell to zsh for root and user",
        "icon":  "🐚",
    },
    {
        "id":    "go_env",
        "label": "Go Environment",
        "desc":  "Set GOPATH, GOMODCACHE via go env -w",
        "icon":  "⚙️",
    },
    {
        "id":    "virtualbox",
        "label": "VirtualBox Repo",
        "desc":  "Add official VirtualBox apt repo and install virtualbox-7.1",
        "icon":  "📦",
    },
    {
        "id":    "docker",
        "label": "Docker CE",
        "desc":  "Install Docker, add user to docker group",
        "icon":  "🐳",
    },
    {
        "id":    "extras",
        "label": "Extras",
        "desc":  "Brave, Bangla fonts, Ollama + models, Snap apps, purge parrot-updater",
        "icon":  "🎁",
    },
    {
        "id":    "pip",
        "label": "Pip Packages",
        "desc":  "pwntools, flask, django, flask_sqlalchemy, waymore",
        "icon":  "🐍",
    },
]


def select_modules() -> list[str]:
    """
    Interactive checklist. Returns list of selected module IDs.
    All modules are pre-selected by default.
    """
    selected = set(m["id"] for m in MODULES)

    while True:
        clear()
        print_banner()

        print(f"  {Colors.BOLD}Select modules to install:{Colors.RESET}")
        print(f"  {Colors.DIM}Use number to toggle | A = all | N = none | Enter = confirm{Colors.RESET}\n")

        for i, mod in enumerate(MODULES, 1):
            tick  = f"{Colors.GREEN}✔{Colors.RESET}" if mod["id"] in selected else f"{Colors.DIM}○{Colors.RESET}"
            label = f"{Colors.BOLD}{mod['label']}{Colors.RESET}"
            desc  = f"{Colors.DIM}{mod['desc']}{Colors.RESET}"
            print(f"  [{tick}] {i}. {mod['icon']}  {label}")
            print(f"            {desc}\n")

        print(f"  {Colors.YELLOW}──────────────────────────────────────────────{Colors.RESET}")
        print(f"  {Colors.CYAN}[A]{Colors.RESET} Select All  "
              f"{Colors.CYAN}[N]{Colors.RESET} Deselect All  "
              f"{Colors.CYAN}[Q]{Colors.RESET} Quit\n")

        choice = input(f"  {Colors.BOLD}→ {Colors.RESET}").strip().lower()

        if choice == "":
            if not selected:
                print(f"\n  {Colors.RED}Nothing selected. Pick at least one module.{Colors.RESET}")
                input("  Press Enter to continue...")
                continue
            break
        elif choice == "a":
            selected = set(m["id"] for m in MODULES)
        elif choice == "n":
            selected = set()
        elif choice == "q":
            print(f"\n  {Colors.YELLOW}Aborted.{Colors.RESET}\n")
            sys.exit(0)
        elif choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(MODULES):
                mid = MODULES[idx]["id"]
                if mid in selected:
                    selected.discard(mid)
                else:
                    selected.add(mid)
        else:
            pass  # ignore invalid input

    return [m["id"] for m in MODULES if m["id"] in selected]


def confirm_run(selected: list[str]) -> bool:
    """Final confirmation before running."""
    clear()
    print_banner()

    labels = {m["id"]: m["label"] for m in MODULES}

    print(f"  {Colors.BOLD}Ready to install:{Colors.RESET}\n")
    for mid in selected:
        print(f"    {Colors.GREEN}✔{Colors.RESET}  {labels.get(mid, mid)}")

    print(f"\n  {Colors.YELLOW}This will run sudo commands and modify your system.{Colors.RESET}")
    answer = input(f"\n  {Colors.BOLD}Proceed? [y/N]: {Colors.RESET}").strip().lower()
    return answer == "y"


def dry_run_prompt() -> bool:
    """Ask if user wants a dry run."""
    answer = input(
        f"\n  {Colors.CYAN}Run in DRY RUN mode? (shows commands without executing) [y/N]: {Colors.RESET}"
    ).strip().lower()
    return answer == "y"

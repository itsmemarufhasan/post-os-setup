# Parrot OS Post-Install Setup Tool

A clean, modular Python tool to configure your Parrot Security OS from scratch after a fresh install.

---

## Project Structure

```
parrot-setup/
├── setup.py                  ← entry point, run this
├── requirements.txt
├── config/
│   └── tools.yaml            ← ALL your tools live here, edit this
├── modules/
│   ├── logger.py             ← colored output + log file
│   ├── runner.py             ← subprocess execution engine
│   ├── installers.py         ← apt / deb / go / shell / github installers
│   └── tui.py                ← interactive terminal menu
├── logs/
│   └── setup.log             ← auto-created on first run
├── deb/                      ← put your .deb files here
├── tools/                    ← put pre-cloned github tools here
└── my_shell/                 ← put your dotfiles here
    ├── bashrc
    ├── zshrc
    └── root-zshrc
```

---

## Setup

```bash
# 1. Install Python dependency
pip install pyyaml --break-system-packages

# 2. Put your files in place
#    - .deb files → deb/
#    - pre-cloned tools → tools/
#    - dotfiles → my_shell/

# 3. Edit config (set your username, add/remove tools)
nano config/tools.yaml

# 4. Run
python3 setup.py
```

---

## Usage

```bash
# Normal interactive run
python3 setup.py

# Use a different config file
python3 setup.py --config /path/to/other.yaml

# Dry run (see all commands without executing anything)
python3 setup.py --dry-run
```

---

## How It Works

1. **TUI Menu** — You see a checklist of all modules. Toggle what you want, press Enter.
2. **Dry Run Prompt** — Optional: preview every command before anything touches your system.
3. **Confirm** — One final yes/no before execution starts.
4. **Smart Skip** — Already installed packages are detected and skipped automatically.
5. **Auto Dep Fix** — `.deb` packages that fail due to missing deps are automatically fixed with `apt --fix-broken install` and retried.
6. **Full Logging** — Every action is written to `logs/setup.log` with timestamps.
7. **Summary** — Clean install/skip/fail count at the end.

---

## Adding New Tools

### Add an apt tool:
```yaml
apt:
  - category: "Your Category"
    tools:
      - your-tool-name
```

### Add a .deb package:
```yaml
deb:
  - category: "Your Category"
    packages:
      - file: "yourpackage.deb"
        name: "Human Readable Name"
```

### Add a Go tool:
```yaml
go:
  - category: "Your Category"
    tools:
      - pkg: "github.com/author/tool@latest"
        name: "tool"
```

### Add a dotfile:
```yaml
shell:
  dotfiles:
    - src: "my_shell/yourfile"
      dest: "/home/{username}/.yourfile"
```

---

## Notes

- `{username}` in dotfile paths is auto-replaced with `meta.username` from config.
- Go tools require Go to be installed. The tool will warn you and skip if Go is missing.
- All `sudo` prompts are handled by the underlying commands — the tool itself doesn't store your password.
- The `deb/` directory must contain the actual `.deb` files before running.
- The `tools/` directory must contain your pre-cloned GitHub tools before running.

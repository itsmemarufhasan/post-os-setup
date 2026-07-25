"""
Installer module.
One class per install type: Apt, Deb, Go, Shell, GitHub,
GoEnv, Extras, VirtualBox, Docker.
Each installer returns a results dict: {success, failed, skipped}
"""

import os
import shutil
import subprocess
from pathlib import Path
from modules.logger import SetupLogger
from modules.runner import Runner


def _empty_results() -> dict:
    return {"success": [], "failed": [], "skipped": []}


# ── APT ─────────────────────────────────────────────────────────────────────

class AptInstaller:
    def __init__(self, runner: Runner, logger: SetupLogger):
        self.r   = runner
        self.log = logger

    def update(self):
        self.log.section("Updating apt package lists")
        self.r.run(["sudo", "apt", "update"], label="apt update")
        self.r.run(["sudo", "parrot-upgrade"], label="apt upgrade")

    def fix_broken(self):
        self.r.run(
            ["sudo", "apt", "--fix-broken", "install", "-y"],
            label="apt --fix-broken install",
            capture=True,
        )

    def autoremove(self):
        self.r.run(
            ["sudo", "apt", "autoremove", "-y"],
            label="apt autoremove",
            capture=True,
        )

    def install_category(self, category: str, tools: list[str]) -> dict:
        results = _empty_results()
        self.log.section(f"[APT] {category}")

        for tool in tools:
            if self.r.apt_installed(tool):
                self.log.skip(tool)
                results["skipped"].append(tool)
                continue

            ok = self.r.run(
                ["sudo", "apt", "install", tool, "-y"],
                label=f"apt install {tool}",
                capture=True,
            )
            if ok:
                self.log.success(tool)
                results["success"].append(tool)
            else:
                self.log.error(f"Failed: {tool}")
                results["failed"].append(tool)

        return results


# ── DEB ─────────────────────────────────────────────────────────────────────

class DebInstaller:
    def __init__(self, runner: Runner, logger: SetupLogger, deb_dir: str = "deb"):
        self.r       = runner
        self.log     = logger
        self.deb_dir = Path(deb_dir)

    def install_category(self, category: str, packages: list[dict]) -> dict:
        results = _empty_results()
        self.log.section(f"[DEB] {category}")

        for pkg in packages:
            filename = pkg["file"]
            name     = pkg.get("name", filename)
            path     = self.deb_dir / filename

            if not path.exists():
                self.log.warning(f"{name} → file not found: {path}")
                results["skipped"].append(name)
                continue

            ok = self.r.run(
                ["sudo", "dpkg", "--install", str(path)],
                label=f"dpkg install {name}",
                capture=True,
            )
            if ok:
                self.log.success(name)
                results["success"].append(name)
            else:
                # dpkg often fails on missing deps; try to fix
                self.r.run(
                    ["sudo", "apt", "--fix-broken", "install", "-y"],
                    label=f"fixing deps for {name}",
                    capture=True,
                )
                # retry
                ok2 = self.r.run(
                    ["sudo", "dpkg", "--install", str(path)],
                    label=f"dpkg retry {name}",
                    capture=True,
                )
                if ok2:
                    self.log.success(f"{name} (after dep fix)")
                    results["success"].append(name)
                else:
                    self.log.error(f"Failed: {name}")
                    results["failed"].append(name)

        return results


# ── GO ──────────────────────────────────────────────────────────────────────

class GoInstaller:
    def __init__(self, runner: Runner, logger: SetupLogger):
        self.r   = runner
        self.log = logger

    def _go_env(self) -> dict:
        env = os.environ.copy()
        # Ask Go itself what GOPATH is — respects `go env -w` settings
        result = subprocess.run(
            ["go", "env", "GOPATH"],
            capture_output=True, text=True
        )
        gopath = result.stdout.strip() or str(Path.home() / "go")
        go_bin = str(Path(gopath) / "bin")
        path   = env.get("PATH", "")
        if go_bin not in path:
            env["PATH"] = f"{go_bin}:{path}"
        env["GOPATH"] = gopath
        return env

    def check_go(self) -> bool:
        if not self.r.binary_exists("go"):
            self.log.error("Go is not installed. Install Go first, then re-run.")
            return False
        return True

    def install_category(self, category: str, tools: list[dict]) -> dict:
        results = _empty_results()
        self.log.section(f"[GO] {category}")
        env = self._go_env()

        for tool in tools:
            pkg  = tool["pkg"]
            name = tool.get("name", pkg.split("/")[-1].split("@")[0])

            if self.r.binary_exists(name):
                self.log.skip(name)
                results["skipped"].append(name)
                continue

            ok = self.r.run(
                ["go", "install", "-v", pkg],
                label=f"go install {name}",
                capture=True,
                env=env,
            )
            if ok:
                self.log.success(name)
                results["success"].append(name)
            else:
                self.log.error(f"Failed: {name} ({pkg})")
                results["failed"].append(name)

        return results


# ── SHELL ────────────────────────────────────────────────────────────────────

class ShellInstaller:
    def __init__(self, runner: Runner, logger: SetupLogger, username: str):
        self.r        = runner
        self.log      = logger
        self.username = username

    def install(self, config: dict) -> dict:
        results = _empty_results()
        self.log.section("[SHELL] Applying dotfiles and changing default shell")

        dotfiles = config.get("dotfiles", [])
        for entry in dotfiles:
            src  = Path(entry["src"])
            dest = Path(entry["dest"].replace("{username}", self.username))

            if not src.exists():
                self.log.warning(f"Dotfile not found: {src}")
                results["skipped"].append(str(src))
                continue

            try:
                dest.parent.mkdir(parents=True, exist_ok=True)
                if str(dest).startswith("/root"):
                    self.r.run(
                        ["sudo", "cp", str(src), str(dest)],
                        label=f"copy {src.name} → {dest}",
                        capture=True,
                    )
                else:
                    shutil.copy2(src, dest)
                self.log.success(f"{src.name} → {dest}")
                results["success"].append(str(src.name))
            except Exception as e:
                self.log.error(f"Failed to copy {src}: {e}")
                results["failed"].append(str(src.name))

        # Change shell for root
        if config.get("change_root_shell"):
            shell = "/usr/bin/zsh"
            ok = self.r.run(
                ["sudo", "chsh", "-s", shell, "root"],
                label="chsh root → zsh",
                capture=True,
            )
            if ok:
                self.log.success("Root shell changed to zsh")
                results["success"].append("root shell")
            else:
                self.log.error("Failed to change root shell")
                results["failed"].append("root shell")

        # # Change shell for user
        # if config.get("change_user_shell"):
        #     shell = "/usr/bin/zsh"
        #     ok = self.r.run(
        #         ["sudo", "chsh", "-s", shell, self.username],
        #         label=f"chsh {self.username} → zsh",
        #         capture=True,
        #     )
        #     if ok:
        #         self.log.success(f"{self.username} shell changed to zsh")
        #         results["success"].append(f"{self.username} shell")
        #     else:
        #         self.log.error(f"Failed to change {self.username} shell")
        #         results["failed"].append(f"{self.username} shell")

        return results


# ── GITHUB TOOLS ─────────────────────────────────────────────────────────────

class GitHubInstaller:
    def __init__(self, runner: Runner, logger: SetupLogger):
        self.r   = runner
        self.log = logger

    def move_tools(self, source_dir: str, dest_dir: str) -> dict:
        results = _empty_results()
        self.log.section(f"[GITHUB] Moving tools: {source_dir}/ → {dest_dir}/")

        src = Path(source_dir)
        dst = Path(dest_dir)

        if not src.exists() or not any(src.iterdir()):
            self.log.warning(f"Source directory empty or missing: {src}")
            results["skipped"].append(source_dir)
            return results

        ok = self.r.run(
            ["sudo", "mv"] + [str(p) for p in src.iterdir()] + [str(dst)],
            label=f"mv {source_dir}/* → {dest_dir}/",
            capture=True,
        )
        if ok:
            self.log.success(f"Tools moved to {dest_dir}/")
            results["success"].append("github tools")
        else:
            self.log.error("Failed to move github tools")
            results["failed"].append("github tools")

        return results


# ── GO ENV ───────────────────────────────────────────────────────────────────

class GoEnvInstaller:
    """
    Sets persistent Go environment variables using `go env -w`.
    These are written to $GOENV (usually ~/.config/go/env) and survive reboots.

    Why NOT /usr/local/go as GOPATH:
      /usr/local/go is where the Go compiler itself is installed.
      Using it as GOPATH causes permission errors and path collisions.
      Correct GOPATH is /root/go (for root) or ~/go (for user).
    """

    def __init__(self, runner: Runner, logger: SetupLogger):
        self.r   = runner
        self.log = logger

    def configure(self, config: dict) -> dict:
        results = _empty_results()
        self.log.section("[GO ENV] Configuring Go environment")

        if not self.r.binary_exists("go"):
            self.log.error("Go is not installed — cannot configure Go env.")
            results["failed"].append("go env")
            return results

        env_vars = config.get("env_vars", {})
        for key, value in env_vars.items():
            ok = self.r.run(
                ["go", "env", "-w", f"{key}={value}"],
                label=f"go env -w {key}={value}",
                capture=True,
            )
            if ok:
                self.log.success(f"go env: {key} = {value}")
                results["success"].append(key)
            else:
                self.log.error(f"Failed to set go env: {key}")
                results["failed"].append(key)

        return results


# ── EXTRAS ───────────────────────────────────────────────────────────────────

class ExtrasInstaller:
    """
    Handles one-off setup tasks that don't fit neatly into apt/deb/go:
      - Brave browser (curl install script)
      - Bangla fonts (wget + chmod + execute)
      - Parrot updater purge
      - Ollama install + model pulls + disable autostart
      - Snap packages
    """

    def __init__(self, runner: Runner, logger: SetupLogger):
        self.r   = runner
        self.log = logger

    def install(self, config: dict) -> dict:
        results = _empty_results()
        self.log.section("[EXTRAS] Miscellaneous setup tasks")

        # ── Brave Browser ────────────────────────────────────────────────────
        if config.get("brave", {}).get("install", False):
            if self.r.binary_exists("brave-browser"):
                self.log.skip("Brave browser")
                results["skipped"].append("brave")
            else:
                self.log.step("Installing Brave browser via install script")
                ok = self.r.run(
                    ["bash", "-c", "curl -fsS https://dl.brave.com/install.sh | sh"],
                    label="Brave browser install",
                )
                if ok:
                    self.log.success("Brave browser")
                    results["success"].append("brave")
                else:
                    self.log.error("Brave browser install failed")
                    results["failed"].append("brave")

        # ── Bangla Fonts ─────────────────────────────────────────────────────
        if config.get("bangla_fonts", {}).get("install", False):
            self.log.step("Installing Bangla fonts (lbfi)")
            cmds = [
                ["bash", "-c",
                 "wget --no-check-certificate "
                 "https://raw.githubusercontent.com/fahadahammed/linux-bangla-fonts/master/dist/lbfi "
                 "-O /tmp/lbfi"],
                ["chmod", "+x", "/tmp/lbfi"],
                ["/tmp/lbfi"],
            ]
            ok = all(self.r.run(c, capture=True) for c in cmds)
            if ok:
                self.log.success("Bangla fonts installed")
                results["success"].append("bangla-fonts")
            else:
                self.log.error("Bangla fonts install failed")
                results["failed"].append("bangla-fonts")

        # ── Purge Parrot Updater ──────────────────────────────────────────────
        if config.get("purge_parrot_updater", False):
            ok = self.r.run(
                ["sudo", "apt", "purge", "parrot-updater", "-y"],
                label="Purging parrot-updater",
                capture=True,
            )
            if ok:
                self.log.success("parrot-updater purged")
                results["success"].append("purge parrot-updater")
            else:
                self.log.warning("parrot-updater purge failed (may not be installed)")
                results["skipped"].append("purge parrot-updater")

        # ── Ollama ───────────────────────────────────────────────────────────
        ollama_cfg = config.get("ollama", {})
        if ollama_cfg.get("install", False):
            if self.r.binary_exists("ollama"):
                self.log.skip("Ollama (already installed)")
                results["skipped"].append("ollama")
            else:
                self.log.step("Installing Ollama")
                ok = self.r.run(
                    ["bash", "-c", "curl -fsSL https://ollama.com/install.sh | sh"],
                    label="Ollama install",
                )
                if ok:
                    self.log.success("Ollama installed")
                    results["success"].append("ollama")
                else:
                    self.log.error("Ollama install failed")
                    results["failed"].append("ollama")
                    # don't try to pull models if install failed
                    ollama_cfg = {}

            # Pull models (only if install succeeded or was already installed)
            for model in ollama_cfg.get("models", []):
                self.log.step(f"Pulling Ollama model: {model}")
                ok = self.r.run(
                    ["ollama", "pull", model],
                    label=f"ollama pull {model}",
                )
                if ok:
                    self.log.success(f"Model pulled: {model}")
                    results["success"].append(f"ollama:{model}")
                else:
                    self.log.error(f"Failed to pull model: {model}")
                    results["failed"].append(f"ollama:{model}")

            # Disable autostart
            if ollama_cfg.get("disable_autostart", True):
                ok = self.r.run(
                    ["sudo", "systemctl", "disable", "ollama"],
                    label="Disabling ollama autostart",
                    capture=True,
                )
                if ok:
                    self.log.success("Ollama autostart disabled (run manually with: ollama serve)")
                    results["success"].append("ollama-autostart-disabled")

        # ── Snap Packages ────────────────────────────────────────────────────
        snap_pkgs = config.get("snap", {}).get("packages", [])
        if snap_pkgs:
            # Make sure snapd is running
            self.r.run(
                ["sudo", "systemctl", "start", "snapd"],
                label="Starting snapd",
                capture=True,
            )
            for pkg in snap_pkgs:
                name    = pkg if isinstance(pkg, str) else pkg.get("name")
                classic = isinstance(pkg, dict) and pkg.get("classic", False)
                cmd     = ["sudo", "snap", "install", name]
                if classic:
                    cmd.append("--classic")

                ok = self.r.run(cmd, label=f"snap install {name}", capture=True)
                if ok:
                    self.log.success(f"snap: {name}")
                    results["success"].append(f"snap:{name}")
                else:
                    self.log.error(f"snap install failed: {name}")
                    results["failed"].append(f"snap:{name}")

        # ── Gem Packages ────────────────────────────────────────────────────
        gem_pkgs = config.get("gems", {}).get("packages", [])
        for pkg in gem_pkgs:
            name = pkg if isinstance(pkg, str) else pkg.get("name")
            classic = isinstance(pkg, dict) and pkg.get("classic", False)
            cmd = ["sudo", "gem", "install", name]
            
            ok = self.r.run(cmd, label=f"gem install {name}", capture=True)
            if ok:
                self.log.success(f"gem: {name}")
                results["success"].append(f"gem:{name}")
            else:
                self.log.error(f"gem install failed: {name}")
                results["failed"].append(f"gem:{name}")

        return results


# ── VIRTUALBOX REPO ───────────────────────────────────────────────────────────

class VirtualBoxInstaller:
    """
    Adds the official VirtualBox apt repository using the modern
    gpg --dearmor method (NOT the deprecated apt-key add).

    Steps:
      1. Download oracle_vbox_2016.asc to /tmp
      2. gpg --dearmor it
      3. Move the .gpg keyring to /usr/share/keyrings/
      4. Write the signed-by repo line to /etc/apt/sources.list.d/
      5. apt update
      6. apt install virtualbox-X.X
    """

    def __init__(self, runner: Runner, logger: SetupLogger):
        self.r   = runner
        self.log = logger

    def install(self, config: dict) -> dict:
        results = _empty_results()
        self.log.section("[VIRTUALBOX] Adding repo and installing")

        version    = config.get("version", "7.1")
        pkg_name   = f"virtualbox-{version}"
        keyring    = "/usr/share/keyrings/virtualbox.gpg"
        sources    = "/etc/apt/sources.list.d/virtualbox.list"
        asc_url    = "https://www.virtualbox.org/download/oracle_vbox_2016.asc"
        repo_url   = "https://download.virtualbox.org/virtualbox/debian"
        tmp_asc    = "/tmp/oracle_vbox_2016.asc"
        tmp_gpg    = "/tmp/oracle_vbox_2016.asc.gpg"

        # Skip if already installed
        if self.r.apt_installed(pkg_name):
            self.log.skip(f"{pkg_name} already installed")
            results["skipped"].append(pkg_name)
            return results

        steps = [
            # Download the key
            (["wget", "-q", asc_url, "-O", tmp_asc],
             "Downloading VirtualBox GPG key"),

            # Convert to binary keyring format
            (["bash", "-c", f"gpg --dearmor < {tmp_asc} > {tmp_gpg}"],
             "Converting key with gpg --dearmor"),

            # Move keyring into place (needs sudo)
            (["sudo", "mv", tmp_gpg, keyring],
             f"Installing keyring → {keyring}"),

            # Write apt sources entry
            (["bash", "-c",
              f'echo "deb [arch=amd64 signed-by={keyring}] {repo_url} bookworm contrib" '
              f'| sudo tee {sources}'],
             "Writing VirtualBox apt source"),

            # Update apt
            (["sudo", "apt", "update"],
             "apt update (VirtualBox repo)"),

            # Install
            (["sudo", "apt", "install", pkg_name, "-y"],
             f"Installing {pkg_name}"),
        ]

        for cmd, label in steps:
            ok = self.r.run(cmd, label=label, capture=True)
            if not ok:
                self.log.error(f"VirtualBox setup failed at: {label}")
                results["failed"].append(pkg_name)
                return results

        self.log.success(f"{pkg_name} installed from official repo")
        results["success"].append(pkg_name)
        return results


# ── DOCKER ───────────────────────────────────────────────────────────────────

class DockerInstaller:
    """
    Installs Docker CE using the official Docker convenience script
    or the full manual repo method (configurable).

    Also handles:
      - Adding user to docker group (so you don't need sudo for docker)
      - Enabling/disabling docker autostart
    """

    def __init__(self, runner: Runner, logger: SetupLogger, username: str):
        self.r        = runner
        self.log      = logger
        self.username = username

    def install(self, config: dict) -> dict:
        results = _empty_results()
        self.log.section("[DOCKER] Installing Docker CE")

        if self.r.binary_exists("docker"):
            self.log.skip("Docker already installed")
            results["skipped"].append("docker")
        else:
            method = config.get("method", "script")  # "script" or "repo"

            if method == "script":
                self.log.step("Installing Docker via official convenience script")
                ok = self.r.run(
                    ["bash", "-c", "curl -fsSL https://get.docker.com | sh"],
                    label="Docker install script",
                )
            else:
                # Manual repo method for full control
                keyring  = "/usr/share/keyrings/docker.gpg"
                sources  = "/etc/apt/sources.list.d/docker.list"
                key_url  = "https://download.docker.com/linux/debian/gpg"
                repo_url = "https://download.docker.com/linux/debian"

                steps = [
                    (["bash", "-c",
                      f"curl -fsSL {key_url} | gpg --dearmor -o {keyring}"],
                     "Adding Docker GPG key"),
                    (["bash", "-c",
                      f'echo "deb [arch=amd64 signed-by={keyring}] {repo_url} bookworm stable" '
                      f'| sudo tee {sources}'],
                     "Writing Docker apt source"),
                    (["sudo", "apt", "update"], "apt update (Docker repo)"),
                    (["sudo", "apt", "install",
                      "docker-ce", "docker-ce-cli",
                      "containerd.io", "docker-buildx-plugin",
                      "docker-compose-plugin", "-y"],
                     "Installing Docker CE"),
                ]
                ok = all(self.r.run(c, label=l, capture=True) for c, l in steps)

            if ok:
                self.log.success("Docker installed")
                results["success"].append("docker")
            else:
                self.log.error("Docker install failed")
                results["failed"].append("docker")
                return results

        # Add user to docker group
        if config.get("add_user_to_group", True) and self.username:
            ok = self.r.run(
                ["sudo", "usermod", "-aG", "docker", self.username],
                label=f"Adding {self.username} to docker group",
                capture=True,
            )
            if ok:
                self.log.success(f"{self.username} added to docker group (re-login to apply)")
                results["success"].append("docker-group")
            else:
                self.log.warning("Failed to add user to docker group")
                results["failed"].append("docker-group")

        # Enable/disable autostart
        autostart = config.get("autostart", False)
        action    = "enable" if autostart else "disable"
        self.r.run(
            ["sudo", "systemctl", action, "docker"],
            label=f"systemctl {action} docker",
            capture=True,
        )
        self.log.success(f"Docker autostart: {action}d")
        results["success"].append(f"docker-autostart-{action}d")

        return results

# ── PIP ──────────────────────────────────────────────────────────────────────

class PipInstaller:
    def __init__(self, runner: Runner, logger: SetupLogger):
        self.r   = runner
        self.log = logger

    def install_category(self, category: str, tools: list[str]) -> dict:
        results = _empty_results()
        self.log.section(f"[PIP] {category}")

        for pkg in tools:
            ok = self.r.run(
                ["pip", "install", pkg, "--break-system-packages"],
                label=f"pip install {pkg}",
                capture=True,
            )
            if ok:
                self.log.success(pkg)
                results["success"].append(pkg)
            else:
                self.log.error(f"Failed: {pkg}")
                results["failed"].append(pkg)

        return results


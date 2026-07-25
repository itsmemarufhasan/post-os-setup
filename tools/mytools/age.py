import os, time, socket, platform, subprocess, getpass as gt, pyautogui as pg
from datetime import datetime
from colorama import Style, Fore, init

def all_var():
    init()
    global green, blue, yellow, magenta, cyan, red, dist_name, use_name, hostname, screen_size, reset, distro_name
    green = Fore.GREEN
    blue = Fore.BLUE
    yellow = Fore.YELLOW
    magenta = Fore.MAGENTA
    cyan = Fore.CYAN
    red = Fore.RED
    Fore.LIME = '\033[38;5;154m'  
    Fore.PINK   = '\033[38;5;213m'   # soft pink
    Fore.ORANGE = '\033[38;5;208m'   # nice orange
    Fore.PURPLE = '\033[38;5;141m'   # pastel purple
    Fore.SKY    = '\033[38;5;117m'   # sky blue
    Fore.GOLD   = '\033[38;5;220m'   # golden yellow
    Fore.TEAL   = '\033[38;5;37m'    # turquoise/teal
    Fore.SALMON = '\033[38;5;203m'   # salmon pink

    dist_name = os.uname().sysname
    distro_name = get_distro_name()
    use_name = os.getlogin()
    hostname = socket.gethostname()
    screen_size = pg.size()
    reset = Style.RESET_ALL

def get_distro_name():
    if os.path.exists('/etc/os-release'):
        with open('/etc/os-release', 'r') as f:
            lines = f.readlines()
            for line in lines:
                if line.startswith('PRETTY_NAME='):
                    distro_name = line.split('=', 1)[1].strip().strip('"')
                    return distro_name
                elif line.startswith('NAME='):
                    distro_name = line.split('=', 1)[1].strip().strip('"')
                    with open('/etc/os-release', 'r') as f2:
                        for line2 in f2.readlines():
                            if line2.startswith('VERSION='):
                                version = line2.split('=', 1)[1].strip().strip('"')
                                return f"{distro_name} {version}"
                    return distro_name
    try:
        import distro
        return f"{distro.name()} {distro.version()}"
    except ImportError:
        pass
    try:
        result = subprocess.run(['lsb_release', '-sd'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            return result.stdout.strip().strip('"')
    except:
        pass
    return f"{platform.system()} {platform.release()}"

def find_oldest_file(path):
    oldest_time = time.time()
    for root, dirs, files in os.walk(path):
        for name in files:
            filepath = os.path.join(root, name)
            try:
                ctime = os.path.getctime(filepath)
                if ctime < oldest_time:
                    oldest_time = ctime
            except:
                pass
    return datetime.fromtimestamp(oldest_time)


def screen_time():
    def get_idle_time_seconds():
        idle_ms = subprocess.check_output(["xprintidle"]).decode().strip()
        return int(idle_ms) / 1000

    def get_uptime_seconds():
        with open("/proc/uptime", "r") as f:
            return float(f.read().split()[0])

    def format_time(seconds):
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        seconds = int(seconds % 60)
        return f"{hours}h {minutes}m {seconds}s"

    uptime = get_uptime_seconds()
    idle = get_idle_time_seconds()
    screen_on_time = uptime - idle

    return format_time(screen_on_time)

def all_print():
    all_var()
    screen_time_on = screen_time()
    oldest = find_oldest_file("/etc")
    now = datetime.now()
    age_days = (now - oldest).days
    width = 55
    print("+" + "-" * (width - 2) + "+")
    print(f"| User Name         : {green}{use_name:<32}{reset}|")
    print("+" + "-" * (width - 2) + "+")
    print(f"| OS Name           : {yellow}{dist_name:<32}{reset}|")
    print("+" + "-" * (width - 2) + "+")
    print(f"| Machine Name      : {cyan}{hostname:<32}{reset}|")
    print("+" + "-" * (width - 2) + "+")
    print(f"| Distro Name       : {Fore.LIME}{distro_name:<32}{reset}|")
    print("+" + "-" * (width - 2) + "+")
    print(f"| Installation Date : {green}{oldest.strftime('%d %B %Y'):<32}{reset}|")
    print("+" + "-" * (width - 2) + "+")
    print(f"| Age               : {red}{f'{age_days} Days':<32}{reset}|")
    print("+" + "-" * (width - 2) + "+")
    print(f"| Screen Time       : {Fore.PINK}{f'{screen_time_on}':<32}{reset}|")
    print("+" + "-" * (width - 2) + "+")
    print(f"| Screen Size       : {blue}{f'{screen_size.width}x{screen_size.height}':<32}{reset}|")
    print("+" + "-" * (width - 2) + "+")

if __name__ == "__main__":
    all_print()
    

#!/usr/bin/env python3
"""
Instagram Username Checker - console edition.

Converted from the original tkinter script. The request + detection logic in
check_username() is copied unchanged from the original; only the labels were
renamed ("free" -> "available").

Run:  python main.py
"""

import os
import signal
import string
import sys
import threading
import time
from collections import deque
from pathlib import Path
from random import choice as pick, choices

try:
    from requests import get as g
    from rich import box
    from rich.align import Align
    from rich.console import Console, Group
    from rich.live import Live
    from rich.panel import Panel
    from rich.progress_bar import ProgressBar
    from rich.text import Text
except ImportError:
    sys.exit("Missing packages. Run this first:  pip install -r requirements.txt")

console = Console()
OUT_DIR = Path(__file__).resolve().parent
RESULT_FILE = OUT_DIR / "result.txt"
ERRORS_FILE = OUT_DIR / "errors.txt"
GENERATED_FILE = OUT_DIR / "generated_usernames.txt"

PURPLE = (168, 85, 247)
BLUE = (59, 130, 246)
STATUS_STYLE = {"available": "bold green", "taken": "bold red", "error": "bold yellow"}
DELAY_CHOICES = (1, 2, 3)  # same options as the original dropdown


# --------------------------------------------------------------------------- #
# THE CHECKER - copied from the original script, unchanged
# (only change: the status label "free" is now "available")
# --------------------------------------------------------------------------- #
def check_username(user):
    try:
        response = g(f"https://www.instagram.com/{user}", timeout=10)
        content = response.text
        if user in content:
            place = content.find(user)
            find = content[place - 9 : place + 10]
            status = "available" if find[1:4] == "url" else "taken"
            result = f"- {user}: {status}"
        else:
            status = "error"
            result = f"- {user}: err: 504"
    except Exception as e:
        status = "error"
        result = f"- {user}: error - {str(e)}"
    return status, result


# --------------------------------------------------------------------------- #
# Username generator - follows Instagram's username rules
# --------------------------------------------------------------------------- #
MIN_LEN, MAX_LEN = 3, 30
LETTERS = string.ascii_lowercase
DIGITS = string.digits
SPECIALS = "._"


def is_valid_username(name):
    """Instagram's rules: 3-30 chars; only a-z 0-9 . _ ; no '..'; no leading/trailing '.'; not only digits."""
    if not (MIN_LEN <= len(name) <= MAX_LEN):
        return False
    if any(c not in LETTERS + DIGITS + SPECIALS for c in name):
        return False
    if ".." in name or name.startswith(".") or name.endswith("."):
        return False
    if not any(c.isalpha() or c == "_" for c in name):     # can't be only digits (needs a letter or "_")
        return False
    return True


def is_clean_generated(name):
    """Stricter than Instagram: generated names must also start AND end with a letter or digit
    (Instagram itself would allow a leading/trailing underscore, but never a period)."""
    return is_valid_username(name) and name[0] not in SPECIALS and name[-1] not in SPECIALS


# Generator types shown in the menu: key -> (label, example, (use_digits, use_special))
GEN_TYPES = {
    "1": ("Letters only", "e.g. zmte", (False, False)),
    "2": ("Letters + numbers", "e.g. k7ap", (True, False)),
    "3": ("Letters + numbers + special", "e.g. a_3x", (True, True)),
    "4": ("Mixed", "random mix of all", None),
}
# "Mixed" picks one of these per username, so some are letters only, some letters + numbers,
# some letters + special characters, and some have all three.
MIXED_KINDS = [(False, False), (True, False), (False, True), (True, True)]


def make_username(length, use_digits, use_special):
    """Builds one username of `length` letters (always), plus at least one digit if use_digits and at
    least one special character (_ or .) if use_special. Specials are never first or last."""
    ends_pool = LETTERS + (DIGITS if use_digits else "")
    mid_pool = ends_pool + (SPECIALS if use_special else "")
    chars = [None] * length
    free = list(range(length))

    def take(positions):
        i = pick(positions)
        free.remove(i)
        return i

    if use_special:
        chars[take([i for i in free if 0 < i < length - 1])] = pick(SPECIALS)
    if use_digits:
        chars[take(free)] = pick(DIGITS)
    chars[take(free)] = pick(LETTERS)
    for i in free:
        chars[i] = pick(ends_pool if i in (0, length - 1) else mid_pool)
    return "".join(chars)


def generate_usernames(num_users, length, gen_type="4"):
    """Returns up to num_users unique usernames of the chosen type that follow Instagram's rules and never
    start or end with "." or "_" (fewer only if that many don't exist for this type and length)."""
    generated_usernames = []
    seen = set()
    attempts = 0
    while len(generated_usernames) < num_users and attempts < num_users * 20 + 100:
        attempts += 1
        kind = GEN_TYPES[gen_type][2] or pick(MIXED_KINDS)
        username = make_username(length, *kind)
        if username in seen or not is_clean_generated(username):
            continue
        seen.add(username)
        generated_usernames.append(username)
    return generated_usernames


# --------------------------------------------------------------------------- #
# Look & feel
# --------------------------------------------------------------------------- #
def _banner_art() -> str:
    try:
        import pyfiglet
    except ImportError:
        return "I G C H E C K"
    for font in ("ansi_shadow", "big", "standard"):
        try:
            return pyfiglet.figlet_format("IGCHECK", font=font)
        except Exception:
            continue
    return "I G C H E C K"


def _gradient(art: str) -> Text:
    lines = art.rstrip("\n").split("\n")
    width = max((len(l) for l in lines), default=1) or 1
    out = Text()
    for line in lines:
        for i, ch in enumerate(line):
            t = i / max(width - 1, 1)
            r, gr, b = (int(a + (z - a) * t) for a, z in zip(PURPLE, BLUE))
            out.append(ch, style=f"rgb({r},{gr},{b})")
        out.append("\n")
    return out


def clear_screen():
    """Wipe the whole screen (and scrollback) so nothing from a previous screen shows through."""
    if os.name == "nt":
        os.system("cls")
    else:
        console.clear()
    if not console.legacy_windows:
        # explicit "erase screen + erase scrollback + cursor home" for terminals where clear alone leaves leftovers
        sys.stdout.write("\x1b[2J\x1b[3J\x1b[H")
        sys.stdout.flush()


def print_banner():
    clear_screen()
    console.print(Align.center(_gradient(_banner_art())))
    console.print(Align.center(Text("Instagram Username Checker",
                                    style="bold rgb(168,85,247)")))
    console.print(Align.center(Text("Console edition", style="rgb(59,130,246)")))
    console.print()


def prompt(where: str = "main") -> str:
    console.print()
    console.print(Text(f"┌──(checker@IGCHECK)-[~/{where}]", style="green"))
    return console.input(Text("└─$ ", style="green")).strip()


def menu_panel(title: str, rows) -> Panel:
    body = Text()
    for i, (key, label, value) in enumerate(rows):
        body.append("├─ " if i < len(rows) - 1 else "└─ ", style="blue")
        body.append("[", style="white")
        body.append(key, style="bold white")
        body.append("] ", style="white")
        body.append(label, style="rgb(80,140,255)")
        if value is not None:
            body.append(f"  {value}", style="bold cyan")
        if i < len(rows) - 1:
            body.append("\n")
    return Panel(body, title=title, border_style="blue", box=box.ROUNDED, width=62, padding=(1, 2))


def fmt_time(seconds: float) -> str:
    s = int(max(seconds, 0))
    h, rem = divmod(s, 3600)
    m, sec = divmod(rem, 60)
    return f"{h}:{m:02d}:{sec:02d}"


def print_footer():
    console.print(Align.center(Text("made by @sovvxe", style="grey50")))


# --------------------------------------------------------------------------- #
# Loading the username file
# --------------------------------------------------------------------------- #
def read_lines(path: Path):
    raw = path.read_bytes()
    if raw.startswith((b"\xff\xfe", b"\xfe\xff")):          # Notepad "Unicode" files
        return raw.decode("utf-16").splitlines()
    try:
        return raw.decode("utf-8-sig").splitlines()
    except UnicodeDecodeError:
        return raw.decode("latin-1").splitlines()


def ask_file():
    console.print(Text("  Drag your .txt file in here (or type its path). Type B to go back.",
                       style="rgb(80,140,255)"))
    while True:
        answer = prompt("load").strip().strip('"').strip("'")
        if answer.lower() in ("b", "back"):
            return None
        path = Path(answer).expanduser()
        if not answer or not path.is_file():
            console.print("\n  [red]File not found. Try again (or B to go back).[/red]")
            continue
        try:
            return path, read_lines(path)
        except OSError as exc:
            console.print(f"\n  [red]Could not read that file: {exc}[/red]")


# --------------------------------------------------------------------------- #
# Live dashboard
# --------------------------------------------------------------------------- #
class Progress:
    def __init__(self, total: int):
        self.total = total
        self.available = []
        self.errors = []
        self.taken = 0
        self.checked = 0
        self.current = "-"
        self.recent = deque(maxlen=8)
        self.start_time = time.time()

    @property
    def error_count(self):
        return len(self.errors)

    def record(self, user, status, result):
        self.checked += 1
        if status == "available":
            self.available.append(user)
        elif status == "taken":
            self.taken += 1
        else:
            self.errors.append(user)
        # errors show their message (e.g. "err: 504"); others just the name
        detail = result.split(": ", 1)[1] if status == "error" and ": " in result else ""
        self.recent.append((user, status, detail))


def render(p: Progress, delay: int) -> Panel:
    elapsed = max(time.time() - p.start_time, 0.001)
    rate = p.checked / elapsed
    pct = (p.checked / p.total * 100) if p.total else 100.0
    eta = (p.total - p.checked) / rate if rate > 0 and p.checked < p.total else None

    head = Text.assemble(("Usernames loaded ", "white"), (f"{p.total}", "bold cyan"),
                         ("   Delay ", "white"), (f"{delay}s", "bold cyan"))
    bar = ProgressBar(total=max(p.total, 1), completed=p.checked, width=50,
                      complete_style="rgb(168,85,247)", finished_style="green")
    progress = Text.assemble(("Checked ", "white"), (f"{p.checked} / {p.total}", "bold white"),
                             (f"   ({pct:.1f}%)", "rgb(80,140,255)"))
    counts = Text.assemble(
        ("AVAILABLE ", "bold green"), (f"{len(p.available):<7}", "green"),
        ("TAKEN ", "bold red"), (f"{p.taken:<7}", "red"),
        ("ERROR ", "bold yellow"), (f"{p.error_count:<7}", "yellow"),
    )
    checking = Text.assemble(("Checking: ", "white"), (p.current, "bold cyan"))
    timing = Text.assemble(
        ("Elapsed ", "white"), (fmt_time(elapsed), "bold white"),
        ("   Speed ", "white"), (f"{rate:.2f}/s", "bold white"),
        ("   ETA ", "white"), (fmt_time(eta) if eta is not None else "--:--", "bold white"),
    )

    parts = [head, Text(""), bar, progress, Text(""), counts, Text(""), checking, timing,
             Text(""), Text("Recent results", style="underline white")]
    # keep the whole panel shorter than the window, otherwise the terminal scrolls and leaves clutter
    room = max(3, min(8, console.size.height - 16))
    recent = list(reversed(p.recent))[:room]
    for user, status, detail in recent:
        line = Text.assemble((f"  [{status.upper()}] ", STATUS_STYLE[status]), (user, "white"))
        if detail:
            line.append(f"  {detail}", style="grey62")
        parts.append(line)
    if not recent:
        parts.append(Text("  waiting for first result...", style="grey50"))

    return Panel(Group(*parts), title="IG USERNAME CHECKER", border_style="blue",
                 box=box.ROUNDED, width=min(max(console.width - 2, 40), 92), padding=(0, 2))


def unique_path(path: Path) -> Path:
    """result.txt -> result (1).txt -> result (2).txt ... so earlier result files are never overwritten."""
    if not path.exists():
        return path
    n = 1
    while True:
        candidate = path.with_name(f"{path.stem} ({n}){path.suffix}")
        if not candidate.exists():
            return candidate
        n += 1


def write_results(p: Progress):
    result_path = unique_path(RESULT_FILE)
    result_path.write_text("".join(n + "\n" for n in p.available), encoding="utf-8")
    errors_path = None
    if p.errors:
        errors_path = unique_path(ERRORS_FILE)
        errors_path.write_text("".join(n + "\n" for n in p.errors), encoding="utf-8")
    return errors_path, result_path


def show_summary(p: Progress, errors_path, interrupted: bool, result_path: Path):
    body = Text()
    body.append("AVAILABLE ", style="bold green"); body.append(f"{len(p.available)}\n", style="green")
    body.append("TAKEN     ", style="bold red"); body.append(f"{p.taken}\n", style="red")
    body.append("ERROR     ", style="bold yellow"); body.append(f"{p.error_count}\n\n", style="yellow")
    body.append(f"Saved available usernames to: {result_path}\n", style="white")
    if errors_path:
        body.append(f"Usernames that errored (re-run these): {errors_path}\n", style="yellow")
    if p.available:
        body.append("\nFirst available names:\n", style="underline white")
        for n in p.available[:10]:
            body.append(f"  {n}\n", style="green")
        if len(p.available) > 10:
            body.append(f"  ... and {len(p.available) - 10} more in {result_path.name}\n", style="grey62")
    title = "STOPPED EARLY" if interrupted else "DONE"
    console.print(Panel(body, title=title, border_style="yellow" if interrupted else "green",
                        box=box.ROUNDED, width=min(max(console.width, 40), 92), padding=(1, 2)))


# --------------------------------------------------------------------------- #
# Running a check (one username at a time, like the original)
# --------------------------------------------------------------------------- #
# --------------------------------------------------------------------------- #
# Save results if the console window is suddenly closed
# --------------------------------------------------------------------------- #
_run = {"progress": None, "saved": False}   # the check that is currently running
_save_lock = threading.Lock()
_keep_alive = []                            # keeps the Windows callback from being garbage collected


def emergency_save():
    """Saves whatever has been checked so far (same numbered result/error files as a normal finish).
    Returns True if something was saved."""
    with _save_lock:
        p = _run["progress"]
        if p is None or _run["saved"] or p.checked == 0:
            return False
        _run["saved"] = True
        try:
            write_results(p)
        except Exception:
            return False
        return True


def _on_close_event(ctrl_type):
    """Windows: 2 = console window closed, 5 = user logging off, 6 = system shutting down.
    (0 = Ctrl+C and 1 = Ctrl+Break are left alone - Ctrl+C already stops safely.)"""
    if ctrl_type in (2, 5, 6):
        if emergency_save():
            time.sleep(1)      # short pause so the files are fully written before the window closes
        return True
    return False


def _on_close_signal(signum, frame):
    """Linux/macOS: terminal closed (SIGHUP) or the program was told to terminate (SIGTERM)."""
    if emergency_save():
        time.sleep(1)
    sys.exit(0)


def install_close_handlers():
    if os.name == "nt":
        try:
            import ctypes
            from ctypes import wintypes
            handler_type = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.DWORD)
            callback = handler_type(_on_close_event)
            _keep_alive.append(callback)
            kernel32 = ctypes.windll.kernel32
            kernel32.SetConsoleCtrlHandler.argtypes = [handler_type, wintypes.BOOL]
            kernel32.SetConsoleCtrlHandler.restype = wintypes.BOOL
            kernel32.SetConsoleCtrlHandler(callback, True)
        except Exception:
            pass               # worst case: no save-on-close, everything else still works
    else:
        for sig_name in ("SIGHUP", "SIGTERM"):
            if hasattr(signal, sig_name):
                try:
                    signal.signal(getattr(signal, sig_name), _on_close_signal)
                except (ValueError, OSError):
                    pass


def run_check(usernames, delay: int):
    names = [u.strip() for u in usernames if u.strip()]   # same as the original: strip + skip blanks
    if not names:
        console.print("\n  [red]No usernames to check.[/red]")
        console.input("\n  Press Enter to go back...")
        return

    console.print()
    console.input(Text(f"  {len(names)} usernames ready. Press Enter to start (Ctrl+C stops safely)... ",
                       style="rgb(80,140,255)"))
    clear_screen()   # the dashboard gets the whole window to itself

    p = Progress(len(names))
    _run["progress"], _run["saved"] = p, False   # from here on, closing the window saves the results
    interrupted = False
    try:
        with Live(get_renderable=lambda: render(p, delay), console=console, refresh_per_second=8,
                  screen=True):   # own full-screen view: nothing from it is left behind afterwards
            for i, user in enumerate(names):
                p.current = user
                status, result = check_username(user)
                p.record(user, status, result)
                if i < len(names) - 1:
                    time.sleep(delay)
            p.current = "-"
    except KeyboardInterrupt:
        interrupted = True
        pass   # the summary below says the run stopped early

    with _save_lock:         # if the window gets closed right now, the emergency save waits for this one
        _run["saved"] = True
        errors_path, result_path = write_results(p)
    _run["progress"] = None
    print_banner()
    show_summary(p, errors_path, interrupted, result_path)
    console.input("\n  Press Enter to return to the menu...")


# --------------------------------------------------------------------------- #
# Menu flows
# --------------------------------------------------------------------------- #
def check_file_flow(delay: int):
    print_banner()
    loaded = ask_file()
    if loaded is None:
        return
    path, lines = loaded
    count = len([l for l in lines if l.strip()])
    console.print()
    console.print(Text.assemble(("  File: ", "white"), (path.name, "bold white"),
                                ("   Usernames found: ", "white"), (f"{count}", "bold green")))
    run_check(lines, delay)


def ask_int(label: str) -> int:
    answer = console.input(Text(f"  {label}: ", style="rgb(80,140,255)")).strip()
    try:
        return int(answer or 0)           # blank counts as 0, like the original
    except ValueError:
        console.print("  [red]Please enter a whole number.[/red]")
        return 0


def choose_generator_type():
    """Shows the 4 generator options on a clean screen. Returns '1'-'4', or None for Back."""
    error = ""
    while True:
        print_banner()
        rows = [(key, label, example) for key, (label, example, _kind) in GEN_TYPES.items()]
        rows.append(("B", "Back", None))
        console.print(menu_panel("USERNAME GENERATOR", rows))
        if error:
            console.print(f"\n  [red]{error}[/red]")
        answer = prompt("generate").lower()
        if answer in GEN_TYPES:
            return answer
        if answer in ("b", "back"):
            return None
        error = "Please choose 1, 2, 3, 4 or B."


def generate_flow(delay: int):
    gen_type = choose_generator_type()
    if gen_type is None:
        return
    label = GEN_TYPES[gen_type][0]

    print_banner()
    console.print(Text.assemble(("  Generator: ", "white"), (label, "bold cyan"),
                                (f"   (length {MIN_LEN}-{MAX_LEN})", "grey62")))
    console.print()
    length = ask_int("Length of usernames")
    num_users = ask_int("Number of usernames")
    if num_users <= 0 or not (MIN_LEN <= length <= MAX_LEN):
        console.print(f"\n  [red]Number must be above 0 and length must be {MIN_LEN}-{MAX_LEN} "
                      "(Instagram's limits).[/red]")
        console.input("\n  Press Enter to go back...")
        return
    names = generate_usernames(num_users, length, gen_type)
    if not names:
        console.print("\n  [red]Nothing could be generated.[/red]")
        console.input("\n  Press Enter to go back...")
        return
    GENERATED_FILE.write_text("".join(n + "\n" for n in names), encoding="utf-8")
    console.print()
    note = ("" if len(names) == num_users
            else f" (only {len(names)} of {num_users} possible for this type and length)")
    console.print(Text(f"  Generated {len(names)} {label.lower()} usernames{note}, "
                       f"saved to {GENERATED_FILE.name}. Preview:", style="white"))
    console.print()
    for n in names[:8]:
        console.print(Text(f"    {n}", style="cyan"))
    if len(names) > 8:
        console.print(Text(f"    ... and {len(names) - 8} more", style="grey62"))
    console.print()
    answer = console.input(Text("  Check them now? (y/n): ", style="rgb(80,140,255)")).strip().lower()
    if answer in ("y", "yes"):
        run_check(names, delay)


def settings_flow(delay: int) -> int:
    while True:
        print_banner()
        console.print(menu_panel("SETTINGS", [
            ("1", "Delay between requests (seconds)", delay),
            ("B", "Back", None),
        ]))
        choice = prompt("settings").lower()
        if choice == "1":
            console.print()
            answer = console.input(Text(f"  Choose a delay {list(DELAY_CHOICES)}: ",
                                        style="rgb(80,140,255)")).strip()
            if answer.isdigit() and int(answer) in DELAY_CHOICES:
                delay = int(answer)
            else:
                console.print(f"\n  [red]Pick one of {list(DELAY_CHOICES)}.[/red]")
                time.sleep(1)
        elif choice in ("b", "back"):
            return delay


def main():
    install_close_handlers()
    delay = 1  # original default
    while True:
        print_banner()
        console.print(menu_panel("MAIN MENU", [
            ("1", "Check usernames from a .txt file", None),
            ("2", "Generate random usernames", None),
            ("3", "Settings", None),
            ("4", "Exit", None),
        ]))
        print_footer()
        try:
            choice = prompt("main").lower()
        except (KeyboardInterrupt, EOFError):
            break
        if choice == "1":
            check_file_flow(delay)
        elif choice == "2":
            generate_flow(delay)
        elif choice == "3":
            delay = settings_flow(delay)
        elif choice in ("4", "e", "exit", "q"):
            break
    console.print("\n  [blue]Bye![/blue]")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[blue]Bye![/blue]")
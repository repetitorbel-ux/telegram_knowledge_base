import subprocess
import sys
from pathlib import Path


DEFAULT_PWSH_EXE = r"C:\Program Files\PowerShell\7\pwsh.exe"


def main() -> int:
    if len(sys.argv) >= 2 and not sys.argv[1].startswith("-"):
        command = sys.argv[1:]
    else:
        task_name = "tg-kb-bot"
        if len(sys.argv) >= 3 and sys.argv[1] == "--task-name":
            task_name = sys.argv[2]

        repo_root = Path(__file__).resolve().parents[1]
        watchdog_script = repo_root / "scripts" / "runtime_watchdog_restart.ps1"
        command = [
            DEFAULT_PWSH_EXE,
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(watchdog_script),
            "-TaskName",
            task_name,
            "-RepoRoot",
            str(repo_root),
        ]

    completed = subprocess.run(
        command,
        creationflags=subprocess.CREATE_NO_WINDOW,
        check=False,
    )
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())

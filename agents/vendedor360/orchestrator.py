#!/usr/bin/env python3
"""
Vendedor 360 orchestrator.

This script runs all active agent bots sequentially. Each bot handles automatic proposal submissions
for a specific procurement platform (e.g. Wherex, Mercado Público, Lissy, Senegocia).

When executed, it imports and runs each bot. If a bot is missing, it logs a warning and continues.

Usage:
    python orchestrator.py
"""

import subprocess
import sys
from pathlib import Path

# Map of agent names to their script paths
AGENTS = {
    "wherex": "agents/wherex/wherex_bot.py",
    # Uncomment or add other agents as they are implemented
    # "mercado_publico": "agents/mercado_publico/mp_bot.py",
    # "senegocia": "agents/senegocia/senegocia_bot.py",
    # "lissy": "agents/lissy/lissy_bot.py",
}

def run_bot(name: str, script_path: str) -> None:
    """Run an individual bot script and report its output."""
    script = Path(script_path)
    if not script.exists():
        print(f"[WARN] {name} bot not found at {script}. Skipping.")
        return
    print(f"[INFO] Running {name} bot: {script}")
    try:
        # Execute the bot using the current Python interpreter
        result = subprocess.run(
            [sys.executable, str(script)],
            capture_output=True,
            text=True,
            check=False,
        )
        print(f"[INFO] {name} bot finished with return code {result.returncode}")
        if result.stdout:
            print(f"[STDOUT] {name} bot:\n{result.stdout}")
        if result.stderr:
            print(f"[STDERR] {name} bot:\n{result.stderr}")
    except Exception as exc:
        print(f"[ERROR] Failed to run {name} bot: {exc}")

def main() -> None:
    """Entry point for orchestrator."""
    print("[INFO] Starting Vendedor 360 orchestrator")
    for name, path in AGENTS.items():
        run_bot(name, path)
    print("[INFO] All bots finished")

if __name__ == "__main__":
    main()

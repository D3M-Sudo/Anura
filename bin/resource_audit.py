import os
from pathlib import Path
import sys
import time

import psutil

# Add repo root to path
sys.path.insert(0, os.getcwd())

from anura.core.silent_runner import SilentRunner
from anura.main import AnuraApplication


def monitor_resources():
    process = psutil.Process(os.getpid())

    print("--- STARTING RESOURCE AUDIT ---")

    # 1. Baseline
    mem_baseline = process.memory_info().rss / 1024 / 1024
    print(f"Baseline Memory: {mem_baseline:.2f} MB")

    # Create App
    app = AnuraApplication(version="audit-test")

    # We use a sample image from the repo
    sample_image = "data/screenshots/anura-window-dark.png"

    if not os.path.exists(sample_image):
        print(f"Error: {sample_image} not found")
        return

    # 2. Run multiple Silent OCR tasks to stress task manager and check for leaks
    iterations = 5
    for i in range(iterations):
        print(f"Iteration {i + 1}/{iterations}...")
        runner = SilentRunner(app, sample_image)
        # We need to mock the actual OCR call if Tesseract isn't available or we want it fast
        # but let's see if it works as is.
        runner.run()

        current_mem = process.memory_info().rss / 1024 / 1024
        print(f"Current Memory: {current_mem:.2f} MB (Delta: {current_mem - mem_baseline:.2f} MB)")
        time.sleep(0.5)

    # 3. Final cleanup
    print("Shutting down app...")
    app.do_shutdown()

    # Give some time for threads to join
    time.sleep(1)

    final_mem = process.memory_info().rss / 1024 / 1024
    print(f"Final Memory: {final_mem:.2f} MB (Leaked: {final_mem - mem_baseline:.2f} MB)")

    # 4. Log Audit
    log_dir = Path.home() / ".local" / "state" / "anura" / "logs"
    log_file = log_dir / "anura.log"
    if log_file.exists():
        print(f"--- LOG AUDIT ({log_file}) ---")
        with open(log_file) as f:
            lines = f.readlines()
            # Show last 20 lines or errors
            for line in lines[-50:]:
                if "ERROR" in line or "WARNING" in line:
                    print(line.strip())
    else:
        print("Log file not generated.")


if __name__ == "__main__":
    monitor_resources()

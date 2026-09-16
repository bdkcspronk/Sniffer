import os
from pathlib import Path
import subprocess
import time
import sys


def has_required_modules(python_executable, required_modules):
    check_command = [
        python_executable,
        '-c',
        'import ' + ','.join(required_modules),
    ]
    result = subprocess.run(
        check_command,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return result.returncode == 0


def find_python_executable(required_modules):
    candidates = [
        sys.executable,
        str(Path(__file__).parent / '.venv' / 'Scripts' / 'python.exe'),
        os.path.expanduser(
            r'~\.platformio\penv\Scripts\python.exe'
        ),
    ]

    checked_candidates = set()
    for candidate in candidates:
        if candidate in checked_candidates:
            continue
        checked_candidates.add(candidate)

        if (
            Path(candidate).is_file()
            and has_required_modules(candidate, required_modules)
        ):
            return candidate

    raise RuntimeError(
        'No Python environment with the required project dependencies was found.'
    )


LOGGER_PYTHON = find_python_executable(('serial',))
PLOTTER_PYTHON = find_python_executable(('pandas', 'matplotlib'))

# Check whether the user passed '--all' to this main script
arguments = sys.argv[1:]

print("=" * 60)
print("  ESP32 SNIFFER & LIVE PLOTTER SCRIPT")
print("=" * 60)

# 1. Start the logging script in the background
print("🚀 Step 1: Starting the logging system in the background...")
log_command = [LOGGER_PYTHON, "filter_logs.py"] + arguments
voice_command = [LOGGER_PYTHON, "voice_announcer.py"]

voice_process = subprocess.Popen(voice_command)
log_process = subprocess.Popen(log_command)

print("   Port COM4 opened and logging live data.")
print("   The graph will now refresh automatically every 30 seconds.")
print("   Press Ctrl+C to stop the ENTIRE system safely.\n")
print("-" * 60)

# 2. Start the infinite loop to generate the graph every 5 minutes
try:
    # Generate an initial graph immediately at startup
    print(f"[{time.strftime('%H:%M:%S')}] Generating initial graph...")
    subprocess.run([PLOTTER_PYTHON, "plot_activity.py"])
    
    while True:
        # Wait 30 seconds (300 seconds)
        # Tip: Change 30 to 300 to test plotting every 300 seconds.
        time.sleep(300) 
        
        print(f"\n[{time.strftime('%H:%M:%S')}] 5 minutes elapsed. Updating graph live...")
        
        # Call plot_activity.py with the default Anaconda Python
        subprocess.run([PLOTTER_PYTHON, "plot_activity.py"])

except KeyboardInterrupt:
    print("\n\n🛑 Ctrl+C detected! Shutting down the system...")
    
    # Close the background logging process cleanly so COM4 becomes available again
    log_process.terminate()
    log_process.wait()
    voice_process.terminate()
    voice_process.wait()
    
    print("🔒 COM4 closed successfully. Logger stopped. Goodbye!")

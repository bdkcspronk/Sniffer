<<<<<<< HEAD
import grp
import subprocess
import time
import sys
import os

# Get the correct Python path from PlatformIO that we used earlier
PIO_PYTHON = r"C:\Users\LEDEN\.platformio\penv\Scripts\python.exe"

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

print("   Port ttyUSB0 opened and logging live data.")
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
    
    # Close the background logging process cleanly so ttyUSB0 becomes available again
    log_process.terminate()
    log_process.wait()
    voice_process.terminate()
    voice_process.wait()
    
    print("🔒 ttyUSB0 closed successfully. Logger stopped. Goodbye!")

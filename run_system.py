import subprocess
import time
import sys
import os

# Haal het juiste Python-pad op van PlatformIO dat we eerder gebruikten
PIO_PYTHON = r"C:\Users\LEDEN\.platformio\penv\Scripts\python.exe"

# Controleer of de gebruiker '--all' heeft meegegeven aan dit hoofdscript
arguments = sys.argv[1:]

print("=" * 60)
print("  ESP32 SNIFFER & LIVE PLOTTER SCRIPT")
print("=" * 60)

# 1. Start het log-script op de achtergrond
print("🚀 Stap 1: Log-systeem opstarten op de achtergrond...")
log_command = [PIO_PYTHON, "filter_logs.py"] + arguments

# subprocess.Popen zorgt ervoor dat het script blijft draaien zonder dit script te blokkeren
log_process = subprocess.Popen(log_command)

print("   Poort COM4 geopend en logt live data.")
print("   Grafiek wordt vanaf nu elke 30 seconden automatisch ververst.")
print("   Druk op Ctrl+C om het HELE systeem veilig te stoppen.\n")
print("-" * 60)

# 2. Start de oneindige loop om elke 5 minuten de grafiek te genereren
try:
    # Genereer direct bij de start alvast een eerste grafiek
    print(f"[{time.strftime('%H:%M:%S')}] Eerste grafiek genereren...")
    subprocess.run(["python", "plot_activity.py"])
    
    while True:
        # Wacht 30 seconden (300 seconden)
        # Tip: Verander 30 naar 300 als je wilt testen of hij elke 300 seconden plot!
        time.sleep(30) 
        
        print(f"\n[{time.strftime('%H:%M:%S')}] 30 seconden voorbij. Grafiek live updaten...")
        
        # Roep plot_activity.py aan met de standaard Anaconda Python
        subprocess.run(["python", "plot_activity.py"])

except KeyboardInterrupt:
    print("\n\n🛑 Ctrl+C gedetecteerd! Systeem aan het afsluiten...")
    
    # Sluit het achtergrond log-proces netjes af zodat COM4 weer vrijkomt
    log_process.terminate()
    log_process.wait()
    
    print("🔒 COM4 succesvol afgesloten. Logger gestopt. Tot ziens!")

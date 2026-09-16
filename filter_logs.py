import json
import serial
import time
import sys

# Controleer of de gebruiker het argument '--all' heeft meegegeven
DISABLE_FILTER = '--all' in sys.argv

# Dictionary om bij te houden wanneer een MAC-adres voor het laatst gelogd is
# Formaat: {"MAC_ADRES": timestamp_in_seconden}
last_logged_time = {}

# Interval in seconden voor de herhaling
# Maximaal 1x per seconde loggen per apparaat
LOG_INTERVAL = 1

# 1. Laad filter.json zodat bekende apparaten altijd een naam kunnen krijgen
mac_to_name = {}

try:
    with open('filter.json', 'r') as f:
        allowed_devices = json.load(f)

    mac_to_name = {
        device['mac'].upper(): device['ssid']
        for device in allowed_devices
        if 'mac' in device and 'ssid' in device
    }

    if DISABLE_FILTER:
        print(
            f"🔓 Filter UITGESCHAKELD: Alle apparaten worden gelogd "
            f"({len(mac_to_name)} bekende apparaten geladen)"
        )
    else:
        print(
            f"🔒 Filter INGESCHAKELD: {len(mac_to_name)} "
            f"apparaten geladen uit filter.json"
        )

except Exception as e:
    if DISABLE_FILTER:
        # Als --all gebruikt wordt, is filter.json niet noodzakelijk.
        print(f"⚠️ filter.json kon niet worden geladen: {e}")
        print("🔓 Filter UITGESCHAKELD: Alle apparaten worden gelogd")
    else:
        print(f"❌ Fout bij het laden van filter.json: {e}")
        sys.exit(1)


# 2. Open de seriële poort (COM4)
try:
    ser = serial.Serial('COM4', 115200, timeout=1)
    print("👂 Listening on COM4... Press Ctrl+C to stop.\n")

except Exception as e:
    print(
        f"❌ Kon COM4 niet openen: {e}. "
        f"Is er nog een andere monitor open?"
    )
    sys.exit(1)


# Bepaal de bestandsnaam op basis van de modus
if DISABLE_FILTER:
    output_filename = 'all_devices_output.jsonl'
else:
    output_filename = 'filtered_output.jsonl'


# 3. Luister live naar de ESP32 en verwerk de data
with open(output_filename, 'a') as log_file:
    while True:
        try:
            if ser.in_waiting > 0:
                line = ser.readline().decode(
                    'utf-8',
                    errors='ignore'
                ).strip()

                # Controleer of de regel het verwachte formaat heeft
                if ',' not in line:
                    continue

                # The firmware emits MAC,RSSI,channel.
                fields = [field.strip() for field in line.split(',')]
                if len(fields) != 3:
                    continue

                mac, rssi, channel = fields

                mac = mac.strip().upper()
                rssi = rssi.strip()

                # Controleer of RSSI een geldig getal is
                try:
                    rssi_value = int(rssi)
                    channel_value = int(channel)
                except ValueError:
                    continue

                current_time = time.time()

                # Controleer RATE-LIMITING:
                # is de wachttijd al voorbij voor dit apparaat?
                if (
                    mac in last_logged_time
                    and (current_time - last_logged_time[mac]) < LOG_INTERVAL
                ):
                    continue

                # 4. Controleer FILTER-MODUS
                if DISABLE_FILTER:
                    # Filter uit:
                    # log ALLE apparaten.
                    #
                    # Als het MAC-adres bekend is in filter.json,
                    # gebruik dan de bekende naam.
                    # Anders "Unknown Device".
                    device_name = mac_to_name.get(
                        mac,
                        "Unknown Device"
                    )

                else:
                    # Filter aan:
                    # log ALLEEN apparaten die in filter.json staan.
                    if mac in mac_to_name:
                        device_name = mac_to_name[mac]
                    else:
                        continue

                # Update de laatst gelogde tijd voor dit apparaat
                last_logged_time[mac] = current_time

                # Bouw het JSON object
                timestamp_str = time.strftime(
                    "%Y-%m-%d %H:%M:%S"
                )

                log_entry = {
                    "timestamp": timestamp_str,
                    "name": device_name,
                    "mac": mac,
                    "rssi": rssi_value,
                    "channel": channel_value
                }

                # Zet het object om naar JSON
                json_string = json.dumps(log_entry)

                # Toon het resultaat
                print(
                    f"[{log_entry['timestamp']}] "
                    f"Spotte: {log_entry['name']} "
                    f"({log_entry['mac']}) | "
                    f"RSSI: {log_entry['rssi']}"
                )

                # Schrijf naar JSONL-bestand
                log_file.write(json_string + '\n')
                log_file.flush()

        except KeyboardInterrupt:
            print("\n🛑 Logger gestopt. Tot ziens!")
            ser.close()
            break

        except Exception:
            # Vang eventuele corrupte seriële regels op
            # zonder de logger te laten crashen.
            pass

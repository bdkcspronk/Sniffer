import json
import pandas as pd
import matplotlib
# Zorg dat er geen pop-up venster opent, zodat het script ongestoord op de achtergrond kan draaien
matplotlib.use('Agg') 
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.patches as patches
from datetime import datetime, time

# 1. Laad filter.json om de handmatige kleuren op te halen
mac_colors = {}
try:
    with open('filter.json', 'r') as f:
        filter_data = json.load(f)
        for device in filter_data:
            if 'mac' in device and 'color' in device:
                mac_colors[device['mac'].upper()] = device['color']
except Exception:
    pass

# 2. Lees de JSONL data in
data = []
try:
    with open('filtered_output.jsonl', 'r') as f:
        for line in f:
            if line.strip():
                data.append(json.loads(line.strip()))
except FileNotFoundError:
    exit()

if not data:
    exit()

# 3. Data verwerken met Pandas
df = pd.DataFrame(data)
df['timestamp'] = pd.to_datetime(df['timestamp'])

# Filter op vandaag
vandaag = datetime.now().date()
df = df[df['timestamp'].dt.date == vandaag]

if df.empty:
    exit()

# Leg de focus op de 5-minuten buckets
df['time_bucket'] = df['timestamp'].dt.floor('5min')
unieke_namen = sorted(df['name'].unique())

# 4. Modern & Slick Plot Design Setup (Premium Dark Minimalist Theme)
plt.style.use('dark_background')
fig, ax = plt.subplots(figsize=(14, 7), facecolor='#0F111A')
ax.set_facecolor('#0F111A')

DEFAULT_COLOR = '#00E676' 
GRID_COLOR = '#263238'   
TEXT_COLOR = '#ECEFF1'   

# Zorg dat gidslijnen achter de balken vallen
ax.set_axisbelow(True)

# 5. Bereken aaneengesloten blokken en plot ze als afgeronde capsules
for y_index, naam in enumerate(unieke_namen):
    persoon_df = df[df['name'] == naam]
    
    # Bepaal de kleur
    sample_mac = persoon_df['mac'].iloc[0].upper() if not persoon_df.empty else ""
    user_color = mac_colors.get(sample_mac, DEFAULT_COLOR)
    
    # Sorteer unieke 5-minuten tijdstippen
    gespotte_tijden = sorted(persoon_df['time_bucket'].unique())
    
    if not gespotte_tijden:
        continue
        
    # Algoritme om opeenvolgende tijdstippen te groeperen tot blokken
    blokken = []
    start_tijd = gespotte_tijden[0]
    vorige_tijd = gespotte_tijden[0]
    
    for actuele_tijd in gespotte_tijden[1:]:
        if actuele_tijd - vorige_tijd <= pd.Timedelta(minutes=10):
            vorige_tijd = actuele_tijd
        else:
            end_tijd = vorige_tijd + pd.Timedelta(minutes=5)
            blokken.append((start_tijd, end_tijd))
            start_tijd = actuele_tijd
            vorige_tijd = actuele_tijd
            
    end_tijd = vorige_tijd + pd.Timedelta(minutes=5)
    blokken.append((start_tijd, end_tijd))
    
    # NIEUW: Teken elk blok als een FancyBboxPatch voor afgeronde hoeken
    for start, end in blokken:
        start_num = mdates.date2num(start)
        end_num = mdates.date2num(end)
        width = end_num - start_num
        
        # y-positie en hoogte van de balk
        height = 0.25
        y_pos = y_index - (height / 2)
        
        # Maak een afgeronde box patch aan
                # Maak een afgeronde box patch aan volgens de nieuwste Matplotlib specificaties
        box = patches.FancyBboxPatch(
            (start_num, y_pos), width, height,
            boxstyle=patches.BoxStyle("Round", pad=0.0, rounding_size=0.0015), # 'rounding_size' vervangt 'radius'
            facecolor=user_color,
            edgecolor='none',
            alpha=0.9,
            zorder=3
        )
        ax.add_patch(box)

# 6. As-instellingen en grenzen (08:00 - 23:59)
ax.set_xlim(mdates.date2num(datetime.combine(vandaag, time(8, 0))), mdates.date2num(datetime.combine(vandaag, time(23, 59))))
ax.set_ylim(-0.75, len(unieke_namen) - 0.25)

# Zet de namen netjes op de Y-as
ax.set_yticks(range(len(unieke_namen)))
ax.set_yticklabels(unieke_namen, fontsize=12, fontweight='500', color=TEXT_COLOR)

# Formatteer de X-as (Tijd) met labels om het uur
ax.xaxis.set_major_locator(mdates.HourLocator(interval=1))
ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
ax.tick_params(axis='x', colors=TEXT_COLOR, labelsize=10, pad=8)
ax.tick_params(axis='y', colors=TEXT_COLOR, pad=12)

# Minimalistische Styling (Verwijder de harde randen / spines)
for spine in ['top', 'right', 'left', 'bottom']:
    ax.spines[spine].set_visible(False)

# Subtiele gidslijnen achter de balken
ax.xaxis.grid(True, linestyle=':', color=GRID_COLOR, alpha=0.7, zorder=1)
ax.yaxis.grid(True, linestyle='-', color=GRID_COLOR, alpha=0.3, zorder=1)

# Strakke hoofdtitel
ax.set_title('FRANCKEN ACTIVITY TRACKER', fontsize=16, fontweight='bold', color=TEXT_COLOR, loc='left', pad=25)

# Zorg dat de tijds-labels elegant schuin staan
fig.autofmt_xdate()
plt.tight_layout()

# Sla de grafiek op
plt.savefig('slide.png', dpi=300, facecolor=fig.get_facecolor(), edgecolor='none')
plt.close(fig)

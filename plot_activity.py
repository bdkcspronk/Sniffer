import json
import colorsys
import hashlib
from pathlib import Path as FilePath

from datetime import datetime, time, timedelta, timezone

import matplotlib

# Prevent a pop-up window so the script can run undisturbed in the background
matplotlib.use('Agg')

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.patches as patches
from matplotlib.path import Path
from matplotlib.transforms import IdentityTransform
import pandas as pd


# Plot configuration
DEFAULT_COLOR = '#00E676'
GRID_COLOR = '#263238'
BACKGROUND_COLOR = "#151722"
TEXT_COLOR = '#ECEFF1'
FALLBACK_SATURATION_RANGE = (0.65, 0.9)
FALLBACK_BRIGHTNESS_RANGE = (0.85, 1.0)
FIGURE_SIZE = (19.2, 10.8)
FIGURE_DPI = 100
CORNER_RADIUS = 8
CURVE_FACTOR = 0.5522848
VERTICAL_AXIS_PADDING = 1.0
SUBPLOT_MARGINS = {
    'left': 0.12,
    'right': 0.98,
    'bottom': 0.12,
    'top': 0.88,
}

# Load custom colors from filter.json.
mac_colors = {}
try:
    with open('filter.json', 'r') as f:
        filter_data = json.load(f)
        for device in filter_data:
            if 'mac' in device and 'color' in device:
                mac_colors[device['mac'].upper()] = device['color']
except Exception:
    pass


def generate_bright_color(identifier):
    """Generate a stable, bright color for an unconfigured device."""
    digest = hashlib.sha256(identifier.encode('utf-8')).digest()
    hue = int.from_bytes(digest[0:2], 'big') / 65535
    saturation_min, saturation_max = FALLBACK_SATURATION_RANGE
    brightness_min, brightness_max = FALLBACK_BRIGHTNESS_RANGE
    saturation = saturation_min + (
        digest[2] / 255 * (saturation_max - saturation_min)
    )
    brightness = brightness_min + (
        digest[3] / 255 * (brightness_max - brightness_min)
    )
    red, green, blue = colorsys.hsv_to_rgb(hue, saturation, brightness)
    return '#{:02X}{:02X}{:02X}'.format(
        round(red * 255),
        round(green * 255),
        round(blue * 255),
    )

# Load activity data.
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

# Prepare the activity data.
df = pd.DataFrame(data)
df['timestamp'] = pd.to_datetime(df['timestamp'])

# Keep only today's activity.
today = datetime.now().date()
df = df[df['timestamp'].dt.date == today]

if df.empty:
    exit()

# Group activity into five-minute buckets.
df['time_bucket'] = df['timestamp'].dt.floor('5min')
unieke_namen = (
    df.groupby('name')['timestamp']
    .min()
    .sort_values()
    .index
    .tolist()
)

# Create the plot.
plt.style.use('dark_background')
fig, ax = plt.subplots(
    figsize=FIGURE_SIZE,
    dpi=FIGURE_DPI,
    facecolor=BACKGROUND_COLOR,
)
ax.set_facecolor(BACKGROUND_COLOR)

# Keep grid lines behind the markers.
ax.set_axisbelow(True)
marker_specs = []
generated_colors = {}

# Build marker specifications for each person.
for y_index, naam in enumerate(unieke_namen):
    persoon_df = df[df['name'] == naam]

    sample_mac = persoon_df['mac'].iloc[0].upper() if not persoon_df.empty else ""
    user_color = mac_colors.get(sample_mac)
    if user_color is None:
        user_color = generated_colors.setdefault(
            sample_mac or naam,
            generate_bright_color(sample_mac or naam),
        )

    spotted_times = sorted(persoon_df['time_bucket'].unique())

    if not spotted_times:
        continue

    blocks = []
    start_time = spotted_times[0]
    previous_time = spotted_times[0]

    for current_time in spotted_times[1:]:
        if current_time - previous_time <= pd.Timedelta(minutes=10):
            previous_time = current_time
        else:
            end_time = previous_time + pd.Timedelta(minutes=5)
            blocks.append((start_time, end_time))
            start_time = current_time
            previous_time = current_time

    end_time = previous_time + pd.Timedelta(minutes=5)
    blocks.append((start_time, end_time))

    for start, end in blocks:
        start_num = mdates.date2num(start)
        end_num = mdates.date2num(end)
        width = end_num - start_num

        height = 0.2 * (len(unieke_namen) + 0.5) / 10.5
        y_pos = y_index - (height / 2)

        marker_specs.append(
            (start_num, end_num, y_pos, height, user_color)
        )

# Configure axis limits.
current_datetime = datetime.now()
ax.set_xlim(
    mdates.date2num(datetime.combine(today, time(8, 0))),
    mdates.date2num(current_datetime + timedelta(minutes=30))
)
ax.set_ylim(
    -VERTICAL_AXIS_PADDING,
    len(unieke_namen) - 1 + VERTICAL_AXIS_PADDING,
)

# Configure Y-axis labels.
ax.set_yticks(range(len(unieke_namen)))
ax.set_yticklabels(
    unieke_namen,
    fontsize=20,
    fontweight='500',
    color=TEXT_COLOR,
)
ax.invert_yaxis()

# Configure X-axis labels.
ax.xaxis.set_major_locator(mdates.HourLocator(interval=1))
ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
ax.tick_params(axis='x', colors=TEXT_COLOR, labelsize=20, pad=8)
ax.tick_params(axis='y', colors=TEXT_COLOR, pad=12)

# Remove plot borders.
for spine in ['top', 'right', 'left', 'bottom']:
    ax.spines[spine].set_visible(False)

# Add X-axis grid lines every 15 minutes, with stronger half-hour and hourly lines.
grid_start = pd.Timestamp(datetime.combine(today, time(8, 0)))
grid_end = pd.Timestamp(current_datetime + timedelta(minutes=5))
for grid_time in pd.date_range(grid_start, grid_end, freq='15min'):
    if grid_time.minute == 0:
        line_width = 2.0
        line_alpha = 0.9
    elif grid_time.minute == 30:
        line_width = 1.3
        line_alpha = 0.75
    else:
        line_width = 0.7
        line_alpha = 0.5

    ax.axvline(
        grid_time,
        linestyle='-',
        linewidth=line_width,
        color=GRID_COLOR,
        alpha=line_alpha,
        zorder=1
    )

# Add subtle horizontal grid lines.
ax.yaxis.grid(True, linestyle='-', color=GRID_COLOR, alpha=0.3, zorder=1)

# Add the title.
ax.set_title(
    'FRANCKEN ACTIVITY TRACKER',
    fontsize=25,
    fontweight='bold',
    color=TEXT_COLOR,
    loc='left',
    pad=25,
)

# Finalize layout before converting marker coordinates to screen space.
fig.autofmt_xdate()
fig.subplots_adjust(**SUBPLOT_MARGINS)

fig.canvas.draw()
data_transform = ax.transData
display_transform = IdentityTransform()

for start_num, end_num, y_pos, height, user_color in marker_specs:
    x0, y0 = data_transform.transform((start_num, y_pos))
    x1, y1 = data_transform.transform((end_num, y_pos + height))
    radius = min(CORNER_RADIUS, abs(x1 - x0) / 2, abs(y1 - y0) / 2)
    x0, x1 = sorted((x0, x1))
    y0, y1 = sorted((y0, y1))
    curve = radius * CURVE_FACTOR

    rounded_path = Path([
        (x0 + radius, y0),
        (x1 - radius, y0),
        (x1 - radius + curve, y0),
        (x1, y0 + radius - curve),
        (x1, y0 + radius),
        (x1, y1 - radius),
        (x1, y1 - radius + curve),
        (x1 - radius + curve, y1),
        (x1 - radius, y1),
        (x0 + radius, y1),
        (x0 + radius - curve, y1),
        (x0, y1 - radius + curve),
        (x0, y1 - radius),
        (x0, y0 + radius),
        (x0, y0 + radius - curve),
        (x0 + radius - curve, y0),
        (x0 + radius, y0),
    ], [
        Path.MOVETO,
        Path.LINETO,
        Path.CURVE4,
        Path.CURVE4,
        Path.CURVE4,
        Path.LINETO,
        Path.CURVE4,
        Path.CURVE4,
        Path.CURVE4,
        Path.LINETO,
        Path.CURVE4,
        Path.CURVE4,
        Path.CURVE4,
        Path.LINETO,
        Path.CURVE4,
        Path.CURVE4,
        Path.CURVE4,
    ])
    box = patches.PathPatch(
        rounded_path,
        transform=display_transform,
        facecolor=user_color,
        edgecolor='none',
        alpha=0.9,
        zorder=3
    )
    ax.add_patch(box)

# Save the graph with a unique UTC timestamped filename.
poster_directory = FilePath.home() / 'tv-posters'
poster_directory.mkdir(parents=True, exist_ok=True)
for old_poster in poster_directory.glob('slide-*.png'):
    if old_poster.is_file():
        old_poster.unlink()

poster_path = poster_directory / (
    f"slide-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ')}.png"
)

plt.savefig(
    poster_path,
    dpi=FIGURE_DPI,
    facecolor=fig.get_facecolor(),
    edgecolor='none',
)
plt.close(fig)

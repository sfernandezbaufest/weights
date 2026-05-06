# Weights

A personal body tracking desktop app built with Python and CustomTkinter. Log your daily weight, manage training phases, record nutritionist measurements, and visualize your progress over time.

![Python](https://img.shields.io/badge/Python-3.10+-c8f500?style=flat-square&labelColor=0a0a0a)
![CustomTkinter](https://img.shields.io/badge/CustomTkinter-5.2+-c8f500?style=flat-square&labelColor=0a0a0a)
![License](https://img.shields.io/badge/License-MIT-c8f500?style=flat-square&labelColor=0a0a0a)

---

## Features

- **Daily weight logging** — add or update today's weight with a single input. Automatically detects if a record already exists for today and switches to update mode.
- **Phase tracking** — manage bulk, cut, and maintenance phases with start dates, end dates, weight goals, and target dates.
- **Nutritionist reports** — record detailed body composition measurements from your nutritionist (body fat %, skeletal muscle mass, visceral fat index, muscle quality, segmental data, and body measurements).
- **Statistics dashboard** — visualize weight evolution with an interactive chart color-coded by training phase, or browse all records in a compact table. Filter by all time, current phase, last month, last year, or current week.
- **Phase overview** — see your current phase goals vs. actual progress, days remaining, and a visual progress bar.
- **Report comparison** — compare all nutritionist reports side by side with color-coded deltas between measurements.
- **AI report export** — generate a structured `.txt` file with all your data to share with an AI for analysis.

---

## Project Structure

```
weights/
├── core/                      # Business logic (no UI)
│   ├── csv_utils.py           # Generic CSV read/write
│   ├── weights.py             # Weight logging and filtering
│   ├── phases.py              # Phase management
│   ├── reports.py             # Nutritionist report logging
│   └── report_generator.py   # AI report text generation
├── data/                      # CSV databases (gitignored)
│   ├── weights.csv
│   ├── phases.csv
│   └── reports.csv
├── ui/
│   └── app.py                 # CustomTkinter UI
├── icon.icns                  # App icon (macOS)
├── requirements.txt
└── README.md
```

---

## Installation

### Requirements

- Python 3.10 or higher
- pip

### Steps

**1. Clone the repository**

```bash
git clone https://github.com/sfernandezbaufest/weights.git
cd weights
```

**2. Install dependencies**

```bash
pip install -r requirements.txt
```

> On macOS with Homebrew Python, you may need to add `--break-system-packages`:
> ```bash
> pip install -r requirements.txt --break-system-packages
> ```

**3. Run the app**

```bash
python3 ui/app.py
```

---

## Usage

### Home screen

The home screen gives you immediate access to the most frequent action — logging your weight. Enter your weight in kg and press **ADD WEIGHT**. If you already logged a weight today, the button switches to **UPDATE WEIGHT**.

The three secondary buttons navigate to:
- **STATISTICS** — charts and tables
- **NEW PHASE** — start a new training phase
- **ADD REPORT** — log a nutritionist measurement
- **AI REPORT** — export all data as a `.txt` file

### Phases

A phase represents a training period (bulk, cut, or maintenance). When you start a new phase, the current active phase is automatically closed with today's date as its end date. Each phase can have a weight goal and a target date.

### Nutritionist reports

Record detailed body composition data from your nutritionist visits. Fields include body fat %, skeletal muscle mass, fat-free mass, visceral fat index, muscle quality, trunk fat, total body water, and body measurements (neck, chest, bicep, hip, thigh).

### Statistics

Navigate to **STATISTICS** from the home screen to access three views:

- **WEIGHT EVOLUTION** — line chart color-coded by phase (green = bulk, red = cut, orange = maintenance) with an interactive hover tooltip showing date and weight. Switch between chart and table view. Filter by: all time, current phase, last month, last year, or current week.
- **CURRENT PHASE** — overview of your active phase with goal vs. actual weight, days remaining, progress since phase start (color-coded green/red depending on phase type), and a temporal progress bar.
- **REPORTS** — side-by-side comparison of all nutritionist reports with color-coded deltas between measurements (green = improvement, red = regression).

### AI report

Press **AI REPORT** on the home screen to generate and save a structured `.txt` file containing all your data — phases, full weight history with stats, and all nutritionist measurements. Ready to paste into any AI for analysis.

---

## Data

All data is stored locally in CSV files inside the `data/` folder. The folder is included in `.gitignore` so your personal data is never pushed to the repository. When a new user clones the repo, the `data/` folder is empty and gets populated as they use the app.

---

## Dependencies

| Package | Purpose |
|---|---|
| `customtkinter` | Modern dark UI framework |
| `matplotlib` | Charts and data visualization |
| `pillow` | Image handling (app icon) |

---

## Contributing

This is a personal project but feel free to fork it and adapt it to your own tracking needs.

---

## License

MIT
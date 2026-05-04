import os
from datetime import datetime
from csv_utils import read_csv, write_csv

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PHASES_CSV_PATH = os.path.join(BASE_DIR, "data", "phases.csv")

FIELD_NAMES = ["start_date", "end_date", "phase_type", "weight_goal", "date_goal"]

def update_phase(phase_type, weight_goal, date_goal) -> None:

    current_date = datetime.now().strftime("%d/%m/%y")
    phases_list = read_csv(PHASES_CSV_PATH)

    phases_list[-1]["end_date"] = current_date
    phases_list.append({
        "start_date": current_date,
        "end_date": "",
        "phase_type": phase_type,
        "weight_goal": weight_goal,
        "date_goal": date_goal
    })

    write_csv(phases_list, PHASES_CSV_PATH, FIELD_NAMES)

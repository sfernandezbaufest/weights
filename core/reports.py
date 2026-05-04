import os
from datetime import datetime
from csv_utils import read_csv, write_csv

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPORTS_CSV_PATH = os.path.join(BASE_DIR, "data", "reports.csv")

FIELD_NAMES = ["date", "body_fat_pct", "skeletal_muscle_mass", "fat_free_mass", "visceral_fat_index", "muscle_quality",
               "trunk_fat_kg", "trunk_fat_pct", "total_body_water"]

def add_report(report_data: dict) -> None:

    current_date = datetime.now().strftime("%d/%m/%y")
    reports_list = read_csv(REPORTS_CSV_PATH)

    report_data["date"] = current_date
    reports_list.append(report_data)

    write_csv(reports_list, REPORTS_CSV_PATH, FIELD_NAMES)
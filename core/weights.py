import os
from datetime import datetime, timedelta
from core.csv_utils import read_csv, write_csv

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WEIGHTS_CSV_PATH = os.path.join(BASE_DIR, "data", "weights.csv")
PHASES_CSV_PATH = os.path.join(BASE_DIR, "data", "phases.csv")
FIELD_NAMES = ["date", "weight"]


def add_weight(new_weight: float) -> str:
    """
    Añade o actualiza el peso de hoy en el CSV.
    Devuelve "updated" si ya había un registro hoy,
    o "added" si es una entrada nueva.
    """
    current_date = datetime.now().strftime("%d/%m/%y")
    weights_list = read_csv(WEIGHTS_CSV_PATH)

    if weights_list and weights_list[-1]["date"] == current_date:
        weights_list[-1]["weight"] = f"{new_weight:.2f}"
        result = "updated"
    else:
        weights_list.append({"date": current_date, "weight": f"{new_weight:.2f}"})
        result = "added"

    write_csv(weights_list, WEIGHTS_CSV_PATH, FIELD_NAMES)
    return result

def get_today_weight() -> float | None:
    """
    Devuelve el peso de hoy si existe, o None si no hay registro.
    """
    weights_list = read_csv(WEIGHTS_CSV_PATH)
    current_date = datetime.now().strftime("%d/%m/%y")

    if weights_list and weights_list[-1]["date"] == current_date:
        return float(weights_list[-1]["weight"])
    return None

def get_all_weights() -> list[dict]:
    """
    Devuelve todos los registros con fechas como objetos datetime.
    """
    raw = read_csv(WEIGHTS_CSV_PATH)
    result = []
    for row in raw:
        try:
            result.append({
                "date":   datetime.strptime(row["date"], "%d/%m/%y"),
                "weight": float(row["weight"])
            })
        except (ValueError, KeyError):
            continue
    return result

def get_weights_filtered(mode: str, phase_start: str = None) -> list[dict]:
    """
    Devuelve pesos filtrados según el modo:
    - "all":   todos los registros
    - "week":  semana en curso (lunes a hoy)
    - "phase": desde el start_date de la fase activa
    - "month": último mes
    - "year":  último año
    """
    all_weights = get_all_weights()
    now = datetime.now()

    if mode == "all":
        return all_weights
    elif mode == "week":
        # Lunes de la semana actual
        start_of_week = now - timedelta(days=now.weekday())
        start_of_week = start_of_week.replace(hour=0, minute=0, second=0, microsecond=0)
        return [w for w in all_weights if w["date"] >= start_of_week]
    elif mode == "phase" and phase_start:
        start = datetime.strptime(phase_start, "%d/%m/%y")
        return [w for w in all_weights if w["date"] >= start]
    elif mode == "month":
        cutoff = now - timedelta(days=30)
        return [w for w in all_weights if w["date"] >= cutoff]
    elif mode == "year":
        cutoff = now - timedelta(days=365)
        return [w for w in all_weights if w["date"] >= cutoff]
    return all_weights

def get_weights_with_phase() -> list[dict]:
    weights_data = get_all_weights()
    phases_data  = read_csv(PHASES_CSV_PATH)

    weights_with_phase = []
    for w in weights_data:
        phase_name = "unknown"
        
        for p in phases_data:
            start = datetime.strptime(p["start_date"], "%d/%m/%y")
            end = datetime.strptime(p["end_date"], "%d/%m/%y") if p["end_date"].strip() else datetime.now()
            if start <= w["date"] < end:
                phase_name = p["phase_type"]
                break

        weights_with_phase.append({
            "date":       w["date"],
            "weight":     w["weight"],
            "phase_type": phase_name
        })
    return weights_with_phase           
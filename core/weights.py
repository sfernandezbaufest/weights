import os
from datetime import datetime
from core.csv_utils import read_csv, write_csv

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))       # __file__ es una variable que python crea automaticamente en cada script que es la ruta del archivo que se esta ejecutando
WEIGHTS_CSV_PATH = os.path.join(BASE_DIR, "data", "weights.csv")                  # abspath significa "absolute path" se asegura de que la ruta sea absoluta
                                                                             # dirname significa "directory name" devuelve la ruta del archivo eliminando el nombre del archivo
                                                                             # join construye una ruta uniendo partes con el separador correcto segun el SO
FIELD_NAMES = ["date", "weight"]

def add_weight(new_weight) -> str:
    """
    Añade o actualiza el peso de hoy en el CSV.
    Devuelve "updated" si ya había un registro hoy,
    o "added" si es una entrada nueva.
    """
    current_date = datetime.now().strftime("%d/%m/%y")                        # Averigua la fecha acual en el formato %d/%m/%y
    weights_list = read_csv(WEIGHTS_CSV_PATH)

    if weights_list and weights_list[-1]["date"] == current_date:             # if weights_lis... es para saber si weights_list existe
        weights_list[-1]["weight"] = f"{new_weight:.2f}"
        result = "updated"
    else:
        weights_list.append({
            "date": current_date,
            "weight": f"{new_weight:.2f}"
        })
        result = "added"

    write_csv(weights_list, WEIGHTS_CSV_PATH, FIELD_NAMES)
    return result

def get_today_weight() -> float | None:

    weights_list = read_csv(WEIGHTS_CSV_PATH)
    current_date = datetime.now().strftime("%d/%m/%y")

    if weights_list and weights_list[-1]["date"] == current_date:
        return float(weights_list[-1]["weight"])
    else:
        return None
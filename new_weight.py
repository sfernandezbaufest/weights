import csv
import os
from datetime import datetime

WEIGHTS_CSV = "data/weights.csv"                                               # Variable String que contiene la ruta del archivo, no el archivo en si                                                          # Lista donde se almacenan todos los diccionarios de cada fila

def ask_weight() -> float:
    """
    Pide al usuario su peso.
    Rechaza comas como separador decimal y valores no numéricos.
    """
    while True:
        weight_input = input("Introduce tu peso de hoy: ").strip()

        if "," in weight_input:
            print("❌ Usa punto decimal (.) en lugar de coma (,).")
            continue

        try:
            return float(weight_input)
        except ValueError:
            print("❌ Peso no válido. Introduce solo numeros")

def read_and_save_file() -> list: 
    """
    Lee el CSV y devuelve una lista de diccionarios.
    Si el archivo no existe, devuelve una lista vacía.
    """
    if os.path.exists(WEIGHTS_CSV):                                          # Si el archivo existe lo lee y lo devuelve en forma de lista de diccionarios
        with open(WEIGHTS_CSV, "r", newline="", encoding="utf-8") as f:
            return list(csv.DictReader(f))                                   # No hay que pasar field_names porque solo estamos leyendo
    
    else: 
        return []

def update_weights(weights_list: list, current_date: str, new_weight: float) -> list:
    """
    Decide si se sobrescribe el último peso (misma fecha)
    o si se añade una nueva entrada.
    """
    if weights_list and weights_list[-1]["date"] == current_date:            # if weights_list significa qie si existe weights_list
        weights_list[-1]["weight"] = f"{new_weight:.2f}"
        print("🔁 Peso de hoy actualizado")
    else:
        weights_list.append({
            "date": current_date,
            "weight": f"{new_weight:.2f}"
        })
        print("➕ Nuevo peso añadido")

    return weights_list

def write_CSV(weights_list: list) -> None:
    """
    Escribe el CSV completo a partir de la lista.
    """
    with open(WEIGHTS_CSV, "w", newline="", encoding="utf-8") as f:
        FIELD_NAMES = ["date", "weight"]
        writer = csv.DictWriter(f, fieldnames=FIELD_NAMES)                    # Aqui si hay que pasar FIELD_NAMES porque estamos escribiendo y puede que el archivo este vacio
        writer.writeheader()
        writer.writerows(weights_list)

def main():
    current_date = datetime.now().strftime("%d/%m/%y")                           # Averigua la fecha acual en el formato %d/%m/%y
    new_weight = ask_weight()

    weights_list = read_and_save_file()
    weights_list = update_weights(weights_list, current_date, new_weight)
    write_CSV(weights_list)

if __name__ == "__main__":
    main()







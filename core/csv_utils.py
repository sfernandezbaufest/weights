import csv
import os

def read_csv(path: str) -> list: 
    """
    Lee el CSV y devuelve una lista de diccionarios.
    Si el archivo no existe, devuelve una lista vacía.
    """
    if os.path.exists(path):                                                 # Si el archivo existe lo lee y lo devuelve en forma de lista de diccionarios
        with open(path, "r", newline="", encoding="utf-8") as f:
            return list(csv.DictReader(f))                                   # No hay que pasar field_names porque solo estamos leyendo
    
    else: 
        return []

def write_csv(list_data: list, path: str, field_names: list) -> None:
    """
    Escribe el CSV completo a partir de la lista.
    """
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=field_names)                    # Aqui si hay que pasar FIELD_NAMES porque estamos escribiendo y puede que el archivo este vacio
        writer.writeheader()
        writer.writerows(list_data)
import os
from datetime import datetime
from core.csv_utils import read_csv

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WEIGHTS_CSV_PATH = os.path.join(BASE_DIR, "data", "weights.csv")
REPORTS_CSV_PATH = os.path.join(BASE_DIR, "data", "reports.csv")
PHASES_CSV_PATH = os.path.join(BASE_DIR, "data", "phases.csv")

def generate_report() -> str:

    weights_data = read_csv(WEIGHTS_CSV_PATH)
    reports_data = read_csv(REPORTS_CSV_PATH)
    phases_data = read_csv(PHASES_CSV_PATH)
    
    current_date = datetime.now().strftime("%d/%m/%y")
    report = []
    report.append("=" * 60)
    report.append("INFORME COMPLETO DE SEGUIMIENTO CORPORAL")
    report.append(f"Generado: {current_date}")
    report.append("=" * 60)
    report.append("")
    report.append("-- FASES --")

    for phase in phases_data:
        estado = "ACTIVA" if not phase["end_date"].strip() else "FINALIZADA"
        report.append(f" {phase['start_date']} -> {phase['end_date']}  |  {phase['phase_type'].upper()}  |  Objetivo: {phase['weight_goal']} antes del {phase['date_goal']}  |  [{estado}]\n")

    report.append("-- PESOS --")
    report.append(f"  Total de registros: {len(weights_data)}")
    report.append(f"  Primer registro: {weights_data[0]['date']}  {weights_data[0]['weight']} kg")
    report.append(f"  Último registro:  {weights_data[-1]['date']}  {weights_data[-1]['weight']} kg")

    weights = []
    for row in weights_data:
        weights.append(float(row["weight"]))

    report.append(f"  Mínimo: {min(weights):.2f} kg  |  Máximo: {max(weights):.2f} kg  |  Media: {sum(weights)/len(weights):.2f} kg")

    report.append("")
    report.append("-- HISTORIAL COMPLETO --")
    for row in weights_data:
        report.append(f"{row['date']}  ->  {row['weight']}")

    report.append("")
    report.append("-- MEDICIONES DEL NUTRICIONISTA --")
    for row in reports_data:
        report.append(f"Fecha: {row['date']}")
        report.append(f"  % Grasa corporal: {row['body_fat_pct']}")
        report.append(f"  Masa muscular esquelética (kg): {row['skeletal_muscle_mass']}")
        report.append(f"  Masa libre de grasa (kg): {row['fat_free_mass']}")
        report.append(f"  Índice grasa visceral: {row['visceral_fat_index']}")
        if row['muscle_quality']:
            report.append(f"  Calidad muscular: {row['muscle_quality']}")
        report.append(f"  Grasa tronco (kg): {row['trunk_fat_kg']}")
        report.append(f"  Grasa tronco (%): {row['trunk_fat_pct']}")
        report.append(f"  Agua corporal total (kg): {row['total_body_water']}")
        if row['neck_cm']:
            report.append(f"  Cuello (cm): {row['neck_cm']}")
        if row['chest_cm']:
            report.append(f"  Pecho (cm): {row['chest_cm']}")
        if row['bicep_cm']:
            report.append(f"  Bícep (cm): {row['bicep_cm']}")
        if row['hip_cm']:
            report.append(f"  Cadera (cm): {row['hip_cm']}")
        if row['thigh_cm']:
            report.append(f"  Muslo (cm): {row['thigh_cm']}")
        report.append("")

    report.append("")
    report.append("=" * 60)
    report.append("FIN DEL INFORME")
    report.append("=" * 60)

    return "\n".join(report)             # join es un metodo de string que une una lista de strings en uno solo usando el string sobre el que lo llamas como separador




        
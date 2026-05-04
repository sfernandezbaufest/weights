import customtkinter as ctk
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.weights import add_weight, get_today_weight
from core.phases import update_phase
from core.reports import add_report

# ── Tema ────────────────────────────────────────────────────────────────────
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

BG          = "#0a0a0a"
CARD        = "#141414"
BORDER      = "#333333"
ACCENT      = "#c8f500"
TEXT        = "#e8e8e8"
TEXT_DIM    = "#888888"
HOVER_SEC   = "#1f1f1f"
FONT_MONO   = ("Courier New", 14)
FONT_TITLE  = ("Courier New", 26, "bold")
FONT_LABEL  = ("Courier New", 13)
FONT_SMALL  = ("Courier New", 11)
PAD         = 60   # margen lateral


# ── Vista: Informe ───────────────────────────────────────────────────────────
class ReportView(ctk.CTkFrame):
    def __init__(self, master, on_back):
        super().__init__(master, fg_color=BG)
        self.on_back = on_back

        # Cabecera
        header = ctk.CTkFrame(self, fg_color=BG)
        header.pack(fill="x", padx=PAD, pady=(36, 0))
        ctk.CTkButton(header, text="← VOLVER", font=FONT_SMALL,
                      fg_color="transparent", text_color=TEXT_DIM,
                      hover_color=HOVER_SEC, width=90, height=28,
                      corner_radius=0, command=on_back).pack(side="left")
        ctk.CTkLabel(header, text="// NUEVO INFORME", font=FONT_TITLE,
                     text_color=ACCENT).pack(side="left", padx=16)

        ctk.CTkLabel(self, text="────────────────────────────────",
                     font=FONT_SMALL, text_color=BORDER).pack(pady=(10, 16))

        # Campos en scroll
        self.fields = {}
        field_labels = [
            ("body_fat_pct",        "% GRASA CORPORAL"),
            ("skeletal_muscle_mass","MASA MUSCULAR ESQ. (kg)"),
            ("fat_free_mass",       "MASA LIBRE DE GRASA (kg)"),
            ("visceral_fat_index",  "ÍNDICE GRASA VISCERAL"),
            ("muscle_quality",      "CALIDAD MUSCULAR"),
            ("trunk_fat_kg",        "GRASA TRONCO (kg)"),
            ("trunk_fat_pct",       "GRASA TRONCO (%)"),
            ("total_body_water",    "AGUA CORPORAL TOTAL (kg)"),
            ("neck_cm",             "CUELLO (cm)"),
            ("chest_cm",            "PECHO (cm)"),
            ("bicep_cm",            "BÍCEP (cm)"),
            ("hip_cm",              "CADERA (cm)"),
            ("thigh_cm",            "MUSLO (cm)"),
        ]

        scroll = ctk.CTkScrollableFrame(self, fg_color=BG)
        scroll.pack(fill="both", expand=True, padx=PAD)

        for key, label in field_labels:
            ctk.CTkLabel(scroll, text=label, font=FONT_SMALL,
                         text_color=TEXT_DIM, anchor="w").pack(fill="x", pady=(10, 0))
            entry = ctk.CTkEntry(scroll, font=FONT_MONO,
                                 fg_color=CARD, border_color=BORDER,
                                 text_color=TEXT, height=40)
            entry.pack(fill="x", pady=(2, 0))
            self.fields[key] = entry

        # Botón guardar
        ctk.CTkButton(self, text="GUARDAR INFORME", font=FONT_LABEL,
                      fg_color=ACCENT, text_color=BG,
                      hover_color=BG, border_color=ACCENT, border_width=2,
                      height=50, corner_radius=0,
                      command=self.save).pack(fill="x", padx=PAD, pady=(20, 8))

        self.status = ctk.CTkLabel(self, text="", font=FONT_SMALL, text_color=ACCENT)
        self.status.pack(pady=(0, 16))

    def save(self):
        data = {}
        for key, entry in self.fields.items():
            val = entry.get().strip().replace(",", ".")
            data[key] = float(val) if val else ""
        add_report(data)
        self.status.configure(text="✓  INFORME GUARDADO")
        self.after(1400, self.on_back)


# ── Vista: Fase ──────────────────────────────────────────────────────────────
class PhaseView(ctk.CTkFrame):
    def __init__(self, master, on_back):
        super().__init__(master, fg_color=BG)
        self.on_back = on_back

        # Cabecera
        header = ctk.CTkFrame(self, fg_color=BG)
        header.pack(fill="x", padx=PAD, pady=(36, 0))
        ctk.CTkButton(header, text="← VOLVER", font=FONT_SMALL,
                      fg_color="transparent", text_color=TEXT_DIM,
                      hover_color=HOVER_SEC, width=90, height=28,
                      corner_radius=0, command=on_back).pack(side="left")
        ctk.CTkLabel(header, text="// NUEVA FASE", font=FONT_TITLE,
                     text_color=ACCENT).pack(side="left", padx=16)

        ctk.CTkLabel(self, text="────────────────────────────────",
                     font=FONT_SMALL, text_color=BORDER).pack(pady=(10, 28))

        # Tipo de fase
        ctk.CTkLabel(self, text="TIPO DE FASE", font=FONT_SMALL,
                     text_color=TEXT_DIM, anchor="w").pack(fill="x", padx=PAD)
        self.phase_var = ctk.StringVar(value="bulk")
        seg = ctk.CTkSegmentedButton(self, values=["bulk", "cut", "maintenance"],
                                     variable=self.phase_var,
                                     font=FONT_LABEL,
                                     fg_color=CARD,
                                     selected_color=ACCENT,
                                     selected_hover_color="#a8d400",
                                     unselected_color=CARD,
                                     text_color=BG,
                                     unselected_hover_color=BORDER,
                                     height=44)
        seg.pack(fill="x", padx=PAD, pady=(6, 28))

        # Objetivo de peso
        ctk.CTkLabel(self, text="OBJETIVO DE PESO (kg)", font=FONT_SMALL,
                     text_color=TEXT_DIM, anchor="w").pack(fill="x", padx=PAD)
        self.weight_goal = ctk.CTkEntry(self, font=FONT_MONO,
                                        fg_color=CARD, border_color=BORDER,
                                        text_color=TEXT, height=46)
        self.weight_goal.pack(fill="x", padx=PAD, pady=(6, 24))

        # Fecha objetivo
        ctk.CTkLabel(self, text="FECHA OBJETIVO (dd/mm/aa)", font=FONT_SMALL,
                     text_color=TEXT_DIM, anchor="w").pack(fill="x", padx=PAD)
        self.date_goal = ctk.CTkEntry(self, font=FONT_MONO,
                                      fg_color=CARD, border_color=BORDER,
                                      text_color=TEXT, height=46,
                                      placeholder_text="01/09/26")
        self.date_goal.pack(fill="x", padx=PAD, pady=(6, 36))

        ctk.CTkButton(self, text="INICIAR FASE", font=FONT_LABEL,
                      fg_color=ACCENT, text_color=BG,
                      hover_color=BG, border_color=ACCENT, border_width=2,
                      height=50, corner_radius=0,
                      command=self.save).pack(fill="x", padx=PAD)

        self.status = ctk.CTkLabel(self, text="", font=FONT_SMALL, text_color=ACCENT)
        self.status.pack(pady=12)

    def save(self):
        update_phase(
            phase_type=self.phase_var.get(),
            weight_goal=self.weight_goal.get().strip(),
            date_goal=self.date_goal.get().strip()
        )
        self.status.configure(text="✓  FASE INICIADA")
        self.after(1400, self.on_back)


# ── Vista: Principal ─────────────────────────────────────────────────────────
class HomeView(ctk.CTkFrame):
    def __init__(self, master, on_phase, on_report):
        super().__init__(master, fg_color=BG)

        # Título
        ctk.CTkLabel(self, text="// W E I G H T S", font=FONT_TITLE,
                     text_color=ACCENT).pack(pady=(44, 0))
        ctk.CTkLabel(self, text="────────────────────────────────",
                     font=FONT_SMALL, text_color=BORDER).pack(pady=(8, 32))

        # Estado hoy
        self.today_label = ctk.CTkLabel(self, text="", font=FONT_SMALL,
                                        text_color=ACCENT)
        self.today_label.pack(pady=(0, 8))

        # Label dinámica
        self.action_label = ctk.CTkLabel(self, text="PESO DE HOY (kg)",
                                         font=FONT_SMALL, text_color=TEXT_DIM,
                                         anchor="w")
        self.action_label.pack(fill="x", padx=PAD)

        # Input peso
        self.weight_entry = ctk.CTkEntry(self, font=("Courier New", 22),
                                         fg_color=CARD, border_color=BORDER,
                                         text_color=TEXT, height=60,
                                         justify="center",
                                         placeholder_text="00.00")
        self.weight_entry.pack(fill="x", padx=PAD, pady=(6, 14))

        # Botón principal
        self.action_btn = ctk.CTkButton(self, text="AÑADIR PESO",
                                        font=FONT_LABEL,
                                        fg_color=ACCENT, text_color=BG,
                                        hover_color=BG,
                                        border_color=ACCENT, border_width=2,
                                        height=52, corner_radius=0,
                                        command=self.save_weight)
        self.action_btn.pack(fill="x", padx=PAD)

        self.msg_label = ctk.CTkLabel(self, text="", font=FONT_SMALL,
                                      text_color=ACCENT)
        self.msg_label.pack(pady=8)

        # Separador
        ctk.CTkLabel(self, text="────────────────────────────────",
                     font=FONT_SMALL, text_color=BORDER).pack(pady=(12, 20))

        # Botones secundarios
        ctk.CTkButton(self, text="// NUEVA FASE →", font=FONT_LABEL,
                      fg_color=CARD, text_color=TEXT,
                      border_color=BORDER, border_width=1,
                      hover_color=HOVER_SEC, height=50, corner_radius=0,
                      command=on_phase).pack(fill="x", padx=PAD, pady=(0, 10))

        ctk.CTkButton(self, text="// AÑADIR INFORME →", font=FONT_LABEL,
                      fg_color=CARD, text_color=TEXT,
                      border_color=BORDER, border_width=1,
                      hover_color=HOVER_SEC, height=50, corner_radius=0,
                      command=on_report).pack(fill="x", padx=PAD)

        # Pie
        ctk.CTkLabel(self, text="────────────────────────────────",
                     font=FONT_SMALL, text_color=BORDER).pack(pady=(28, 6))
        ctk.CTkLabel(self, text="sergio / weights v0.1",
                     font=FONT_SMALL, text_color=TEXT_DIM).pack(pady=(0, 16))

        self.check_today()

    def check_today(self):
        today = get_today_weight()
        if today is not None:
            self.today_label.configure(text=f"✓  {today:.2f} kg registrado hoy")
            self.action_label.configure(text="ACTUALIZAR PESO (kg)")
            self.action_btn.configure(text="ACTUALIZAR PESO")
        else:
            self.today_label.configure(text="")
            self.action_label.configure(text="PESO DE HOY (kg)")
            self.action_btn.configure(text="AÑADIR PESO")

    def save_weight(self):
        raw = self.weight_entry.get().strip().replace(",", ".")
        if not raw:
            self.msg_label.configure(text="✗  introduce un peso", text_color="#ff4444")
            return
        try:
            value = float(raw)
        except ValueError:
            self.msg_label.configure(text="✗  valor no válido", text_color="#ff4444")
            return
        result = add_weight(value)
        self.msg_label.configure(
            text="✓  peso actualizado" if result == "updated" else "✓  peso añadido",
            text_color=ACCENT
        )
        self.weight_entry.delete(0, "end")
        self.check_today()


# ── App principal (router) ───────────────────────────────────────────────────
class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("WEIGHTS")
        self.geometry("560x720")
        self.configure(fg_color=BG)
        self.resizable(False, False)
        self.show_home()

    def show_home(self):
        self._clear()
        HomeView(self,
                 on_phase=self.show_phase,
                 on_report=self.show_report).pack(fill="both", expand=True)

    def show_phase(self):
        self._clear()
        PhaseView(self, on_back=self.show_home).pack(fill="both", expand=True)

    def show_report(self):
        self._clear()
        ReportView(self, on_back=self.show_home).pack(fill="both", expand=True)

    def _clear(self):
        for widget in self.winfo_children():
            widget.destroy()


if __name__ == "__main__":
    app = App()
    app.mainloop()
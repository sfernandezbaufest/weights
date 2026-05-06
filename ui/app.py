import customtkinter as ctk
import sys
import os
from PIL import Image, ImageTk
from datetime import datetime, timedelta

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.weights import add_weight, get_today_weight, get_weights_filtered, get_weights_with_phase
from core.phases import update_phase
from core.reports import add_report
from core.report_generator import generate_report
from core.csv_utils import read_csv

import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

BG       = "#0a0a0a"
CARD     = "#141414"
BORDER   = "#333333"
ACCENT   = "#c8f500"
TEXT     = "#e8e8e8"
TEXT_DIM = "#888888"
HOVER_SEC= "#1f1f1f"
PHASE_COLORS = {
    "bulk":        "#c8f500",  # verde lima — volumen
    "cut":         "#ff2d2d",  # rojo vibrante — definición
    "maintenance": "#ff9f00",  # naranja — mantenimiento
    "unknown":     "#888888",  # gris — sin fase
}
FONT_MONO  = ("Courier New", 17)
FONT_TITLE = ("Courier New", 32, "bold")
FONT_LABEL = ("Courier New", 16)
FONT_SMALL = ("Courier New", 14)
FONT_TINY  = ("Courier New", 13)
PAD = 50

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PHASES_CSV_PATH = os.path.join(BASE_DIR, "data", "phases.csv")


def get_active_phase_start() -> str | None:
    phases = read_csv(PHASES_CSV_PATH)
    for p in reversed(phases):
        if not p.get("end_date", "").strip():
            return p.get("start_date", "").strip()
    return None


# ── Vista: Estadísticas ──────────────────────────────────────────────────────
class StatsView(ctk.CTkFrame):
    def __init__(self, master, on_back):
        super().__init__(master, fg_color=BG)
        self.on_back   = on_back
        self.mode      = "all"
        self.view_mode = "chart"
        self._fig      = None
        self._canvas   = None
        self._scatter  = None
        self._chart_dates   = []
        self._chart_weights = []

        header = ctk.CTkFrame(self, fg_color=BG)
        header.pack(fill="x", padx=PAD, pady=(36, 0))
        ctk.CTkButton(header, text="← VOLVER", font=FONT_SMALL,
                      fg_color="transparent", text_color=TEXT_DIM,
                      hover_color=HOVER_SEC, width=90, height=32,
                      corner_radius=0, command=on_back).pack(side="left")
        ctk.CTkLabel(header, text="// ESTADÍSTICAS", font=FONT_TITLE,
                     text_color=ACCENT).pack(side="left", padx=16)

        ctk.CTkLabel(self, text="────────────────────────────────",
                     font=FONT_SMALL, text_color=BORDER).pack(pady=(10, 12))

        controls = ctk.CTkFrame(self, fg_color=BG)
        controls.pack(fill="x", padx=PAD, pady=(0, 12))

        self.view_seg = ctk.CTkSegmentedButton(
            controls, values=["GRÁFICA", "TABLA"],
            command=self._on_view_switch,
            font=FONT_TINY, fg_color=CARD,
            selected_color=ACCENT, selected_hover_color="#a8d400",
            unselected_color=CARD, text_color=BG,
            unselected_hover_color=BORDER, height=38, width=220)
        self.view_seg.set("GRÁFICA")
        self.view_seg.pack(side="left")

        self.filter_var = ctk.StringVar(value="TODO")
        ctk.CTkOptionMenu(
            controls, variable=self.filter_var,
            values=["TODO", "SEMANA EN CURSO", "FASE ACTIVA", "ÚLTIMO MES", "ÚLTIMO AÑO"],
            command=self._on_filter_change,
            font=FONT_TINY, fg_color=CARD,
            button_color=BORDER, button_hover_color=HOVER_SEC,
            text_color=TEXT, dropdown_fg_color=CARD,
            dropdown_text_color=TEXT, dropdown_hover_color=HOVER_SEC,
            height=38, width=220).pack(side="right")

        self.content_frame = ctk.CTkFrame(self, fg_color=BG)
        self.content_frame.pack(fill="both", expand=True, padx=PAD, pady=(0, 20))

        self._tooltip = ctk.CTkLabel(
            self, text="", font=FONT_TINY,
            fg_color=CARD, text_color=TEXT,
            corner_radius=4, padx=10, pady=6)
        self._tooltip.place_forget()

        self._render()

    def _on_view_switch(self, value):
        self.view_mode = "chart" if value == "GRÁFICA" else "table"
        self._render()

    def _on_filter_change(self, value):
        self.mode = {"TODO":"all","SEMANA EN CURSO":"week","FASE ACTIVA":"phase",
                     "ÚLTIMO MES":"month","ÚLTIMO AÑO":"year"}.get(value, "all")
        self._render()

    def _get_data(self):
        phase_start = get_active_phase_start() if self.mode == "phase" else None
        return get_weights_filtered(self.mode, phase_start)

    def _clear_content(self):
        self._tooltip.place_forget()
        if self._fig is not None:
            plt.close(self._fig)
            self._fig = None
            self._canvas = None
            self._scatter = None
        for w in self.content_frame.winfo_children():
            w.destroy()

    def _render(self):
        self._clear_content()
        data = self._get_data()
        if not data:
            ctk.CTkLabel(self.content_frame, text="sin datos para este período",
                         font=FONT_SMALL, text_color=TEXT_DIM).pack(expand=True)
            return
        if self.view_mode == "chart":
            self._render_chart(data)
        else:
            self._render_table(data)

    def _render_chart(self, data):
        dates   = [d["date"] for d in data]
        weights = [d["weight"] for d in data]
        n       = len(dates)
        self._chart_dates   = dates
        self._chart_weights = weights

        self._fig, ax = plt.subplots(figsize=(10, 5))
        self._fig.patch.set_facecolor("#0a0a0a")
        ax.set_facecolor("#0f0f0f")

        # Colores por fase en todos los modos
        data_with_phase = get_weights_with_phase()
        date_set = set(dates)
        phase_map = {row["date"]: row["phase_type"] for row in data_with_phase if row["date"] in date_set}
        point_colors = [PHASE_COLORS.get(phase_map.get(d, "unknown"), ACCENT) for d in dates]

        # Pintar segmento a segmento
        for i in range(len(dates) - 1):
            ax.plot([dates[i], dates[i+1]], [weights[i], weights[i+1]],
                    color=point_colors[i], linewidth=1.8, zorder=3)
        dot_size = 32 if n <= 60 else 0
        self._scatter = ax.scatter(dates, weights, c=point_colors, s=dot_size, zorder=4)

        if self.mode == "all":    margin = 10
        elif self.mode == "year": margin = 5
        else:                     margin = 2
        y_min = min(weights) - margin
        y_max = max(weights) + margin
        ax.fill_between(dates, weights, y_min, alpha=0.08, color=ACCENT)

        span = (dates[-1] - dates[0]).days if n > 1 else 1
        if span <= 7:
            ax.xaxis.set_major_locator(mdates.DayLocator(interval=1))
            ax.xaxis.set_major_formatter(mdates.DateFormatter("%d/%m"))
        elif span <= 31:
            ax.xaxis.set_major_locator(mdates.DayLocator(interval=max(2, span // 8)))
            ax.xaxis.set_major_formatter(mdates.DateFormatter("%d/%m"))
        elif span <= 180:
            ax.xaxis.set_major_locator(mdates.WeekdayLocator(byweekday=0, interval=2))
            ax.xaxis.set_major_formatter(mdates.DateFormatter("%d/%m"))
        elif span <= 400:
            ax.xaxis.set_major_locator(mdates.MonthLocator())
            ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %y"))
        else:
            ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
            ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %y"))

        plt.setp(ax.xaxis.get_majorticklabels(), rotation=40, ha="right",
                 fontsize=11, color=TEXT_DIM, fontfamily="Courier New")
        ax.tick_params(axis="y", colors=TEXT_DIM, labelsize=11)
        for spine in ax.spines.values(): spine.set_edgecolor(BORDER)
        ax.grid(True, color=BORDER, linewidth=0.5, linestyle="--", alpha=0.5)
        ax.set_ylabel("kg", color=TEXT_DIM, fontsize=12, fontfamily="Courier New")
        ax.set_ylim(y_min, y_max)

        w_min = min(weights); w_max = max(weights); w_avg = sum(weights) / n
        ax.set_title(
            f"mín {w_min:.1f}  ·  máx {w_max:.1f}  ·  media {w_avg:.1f}  ·  {n} registros",
            color=TEXT_DIM, fontsize=11, fontfamily="Courier New", pad=10)

        # Leyenda de fases — siempre visible
        import matplotlib.patches as mpatches
        legend_items = [
            mpatches.Patch(color=PHASE_COLORS["bulk"],        label="BULK"),
            mpatches.Patch(color=PHASE_COLORS["cut"],         label="CUT"),
            mpatches.Patch(color=PHASE_COLORS["maintenance"], label="MAINTENANCE"),
        ]
        ax.legend(handles=legend_items, loc="lower left",
                  facecolor="#141414", edgecolor="#333333",
                  labelcolor=TEXT, fontsize=9,
                  prop={"family": "Courier New", "size": 9})

        self._fig.subplots_adjust(left=0.07, right=0.97, top=0.92, bottom=0.18)

        self._canvas = FigureCanvasTkAgg(self._fig, master=self.content_frame)
        self._canvas.draw()
        tk_widget = self._canvas.get_tk_widget()
        tk_widget.pack(fill="both", expand=True)
        self._canvas.mpl_connect("motion_notify_event", self._on_hover)
        tk_widget.bind("<Leave>", lambda e: self._tooltip.place_forget())

    def _on_hover(self, event):
        if event.inaxes is None or self._scatter is None:
            self._tooltip.place_forget(); return
        cont, ind = self._scatter.contains(event)
        if not cont:
            self._tooltip.place_forget(); return
        idx = ind["ind"][0]
        self._tooltip.configure(text=f"{self._chart_dates[idx].strftime('%d/%m/%Y')}   {self._chart_weights[idx]:.2f} kg")
        tk_widget = self._canvas.get_tk_widget()
        win_x = tk_widget.winfo_rootx() + int(event.x) - self.winfo_rootx()
        win_y = tk_widget.winfo_rooty() + (tk_widget.winfo_height() - int(event.y)) - self.winfo_rooty()
        tip_w, tip_h = 240, 36
        tx = win_x + 16 if win_x + 16 + tip_w < self.winfo_width() - 10 else win_x - tip_w - 10
        ty = win_y - tip_h - 10 if win_y - tip_h - 10 > 10 else win_y + 16
        self._tooltip.place(x=tx, y=ty)
        self._tooltip.lift()

    def _render_table(self, data):
        outer = ctk.CTkFrame(self.content_frame, fg_color=BG)
        outer.pack(fill="both", expand=True)
        scroll = ctk.CTkScrollableFrame(outer, fg_color=BG)
        scroll.pack(fill="both", expand=True)

        header = ctk.CTkFrame(scroll, fg_color=CARD)
        header.pack(fill="x", pady=(0, 2))
        ctk.CTkLabel(header, text="FECHA", font=FONT_SMALL, text_color=ACCENT,
                     width=180, anchor="w").pack(side="left", padx=16, pady=10)
        ctk.CTkLabel(header, text="PESO (kg)", font=FONT_SMALL, text_color=ACCENT,
                     anchor="w").pack(side="left", padx=16, pady=10)

        # Construir mapa fecha->fase para colorear filas
        data_with_phase = get_weights_with_phase()
        date_set = {row["date"] for row in data}
        phase_map = {row["date"]: row["phase_type"] for row in data_with_phase if row["date"] in date_set}

        # Colores de fondo muy sutiles (hex con baja opacidad simulada mezclando con BG)
        ROW_BG = {
            "bulk":        "#161f00",  # verde lima muy oscuro
            "cut":         "#1f0000",  # rojo muy oscuro
            "maintenance": "#1f0f00",  # naranja muy oscuro
            "unknown":     BG,
        }

        rows = list(reversed(data))
        def render_batch(start):
            for row in rows[start:start + 20]:
                phase = phase_map.get(row["date"], "unknown")
                row_bg = ROW_BG.get(phase, BG)
                # Acento lateral con el color de fase
                phase_color = PHASE_COLORS.get(phase, ACCENT)

                frame = ctk.CTkFrame(scroll, fg_color=row_bg, height=28)
                frame.pack(fill="x")
                frame.pack_propagate(False)
                # Barra lateral de color
                ctk.CTkFrame(frame, fg_color=phase_color, width=3).pack(side="left", fill="y")
                ctk.CTkLabel(frame, text=row["date"].strftime("%d/%m/%Y"),
                             font=FONT_TINY, text_color=TEXT_DIM,
                             width=180, anchor="w").pack(side="left", padx=16, pady=0)
                ctk.CTkLabel(frame, text=f"{row['weight']:.2f}",
                             font=FONT_MONO, text_color=TEXT,
                             anchor="w").pack(side="left", padx=16, pady=0)
                ctk.CTkFrame(scroll, fg_color=BORDER, height=1).pack(fill="x")
            if start + 20 < len(rows):
                scroll.after(10, lambda s=start: render_batch(s + 20))
        render_batch(0)


# ── Vista: Informe ────────────────────────────────────────────────────────────
class ReportView(ctk.CTkFrame):
    def __init__(self, master, on_back):
        super().__init__(master, fg_color=BG)
        self.on_back = on_back

        header = ctk.CTkFrame(self, fg_color=BG)
        header.pack(fill="x", padx=PAD, pady=(36, 0))
        ctk.CTkButton(header, text="← VOLVER", font=FONT_SMALL,
                      fg_color="transparent", text_color=TEXT_DIM,
                      hover_color=HOVER_SEC, width=90, height=32,
                      corner_radius=0, command=on_back).pack(side="left")
        ctk.CTkLabel(header, text="// NUEVO INFORME", font=FONT_TITLE,
                     text_color=ACCENT).pack(side="left", padx=16)

        ctk.CTkLabel(self, text="────────────────────────────────",
                     font=FONT_SMALL, text_color=BORDER).pack(pady=(10, 16))

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
                                 text_color=TEXT, height=46)
            entry.pack(fill="x", pady=(2, 0))
            self.fields[key] = entry

        ctk.CTkButton(self, text="GUARDAR INFORME", font=FONT_LABEL,
                      fg_color=ACCENT, text_color=BG,
                      hover_color=BG, border_color=ACCENT, border_width=2,
                      height=54, corner_radius=0,
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


# ── Vista: Fase ───────────────────────────────────────────────────────────────
class PhaseView(ctk.CTkFrame):
    def __init__(self, master, on_back):
        super().__init__(master, fg_color=BG)
        self.on_back = on_back

        header = ctk.CTkFrame(self, fg_color=BG)
        header.pack(fill="x", padx=PAD, pady=(36, 0))
        ctk.CTkButton(header, text="← VOLVER", font=FONT_SMALL,
                      fg_color="transparent", text_color=TEXT_DIM,
                      hover_color=HOVER_SEC, width=90, height=32,
                      corner_radius=0, command=on_back).pack(side="left")
        ctk.CTkLabel(header, text="// NUEVA FASE", font=FONT_TITLE,
                     text_color=ACCENT).pack(side="left", padx=16)

        ctk.CTkLabel(self, text="────────────────────────────────",
                     font=FONT_SMALL, text_color=BORDER).pack(pady=(10, 28))

        ctk.CTkLabel(self, text="TIPO DE FASE", font=FONT_SMALL,
                     text_color=TEXT_DIM, anchor="w").pack(fill="x", padx=PAD)
        self.phase_var = ctk.StringVar(value="bulk")
        ctk.CTkSegmentedButton(self, values=["bulk", "cut", "maintenance"],
                               variable=self.phase_var, font=FONT_LABEL,
                               fg_color=CARD, selected_color=ACCENT,
                               selected_hover_color="#a8d400",
                               unselected_color=CARD, text_color=BG,
                               unselected_hover_color=BORDER,
                               height=50).pack(fill="x", padx=PAD, pady=(6, 28))

        ctk.CTkLabel(self, text="OBJETIVO DE PESO (kg)", font=FONT_SMALL,
                     text_color=TEXT_DIM, anchor="w").pack(fill="x", padx=PAD)
        self.weight_goal = ctk.CTkEntry(self, font=FONT_MONO, fg_color=CARD,
                                        border_color=BORDER, text_color=TEXT, height=52)
        self.weight_goal.pack(fill="x", padx=PAD, pady=(6, 24))

        ctk.CTkLabel(self, text="FECHA OBJETIVO (dd/mm/aa)", font=FONT_SMALL,
                     text_color=TEXT_DIM, anchor="w").pack(fill="x", padx=PAD)
        self.date_goal = ctk.CTkEntry(self, font=FONT_MONO, fg_color=CARD,
                                      border_color=BORDER, text_color=TEXT,
                                      height=52, placeholder_text="01/09/26")
        self.date_goal.pack(fill="x", padx=PAD, pady=(6, 36))

        ctk.CTkButton(self, text="INICIAR FASE", font=FONT_LABEL,
                      fg_color=ACCENT, text_color=BG,
                      hover_color=BG, border_color=ACCENT, border_width=2,
                      height=54, corner_radius=0,
                      command=self.save).pack(fill="x", padx=PAD)

        self.status = ctk.CTkLabel(self, text="", font=FONT_SMALL, text_color=ACCENT)
        self.status.pack(pady=12)

    def save(self):
        update_phase(phase_type=self.phase_var.get(),
                     weight_goal=self.weight_goal.get().strip(),
                     date_goal=self.date_goal.get().strip())
        self.status.configure(text="✓  FASE INICIADA")
        self.after(1400, self.on_back)


# ── Vista: Principal ──────────────────────────────────────────────────────────
class HomeView(ctk.CTkFrame):
    def __init__(self, master, on_phase, on_report, on_stats):
        super().__init__(master, fg_color=BG)

        self.pack_propagate(False)
        ctk.CTkLabel(self, text="// W E I G H T S", font=FONT_TITLE,
                     text_color=ACCENT).pack(pady=(44, 0))
        ctk.CTkLabel(self, text="────────────────────────────────",
                     font=FONT_SMALL, text_color=BORDER).pack(pady=(8, 32))

        self.today_label = ctk.CTkLabel(self, text="", font=FONT_SMALL,
                                        text_color=ACCENT)
        self.today_label.pack(pady=(0, 8))

        self.action_label = ctk.CTkLabel(self, text="PESO DE HOY (kg)",
                                         font=FONT_SMALL, text_color=TEXT_DIM, anchor="w")
        self.action_label.pack(fill="x", padx=PAD)

        self.weight_entry = ctk.CTkEntry(self, font=("Courier New", 28),
                                         fg_color=CARD, border_color=BORDER,
                                         text_color=TEXT, height=68,
                                         justify="center", placeholder_text="00.00")
        self.weight_entry.pack(fill="x", padx=PAD, pady=(6, 14))

        self.action_btn = ctk.CTkButton(self, text="AÑADIR PESO", font=FONT_LABEL,
                                        fg_color=ACCENT, text_color=BG,
                                        hover_color=BG, border_color=ACCENT,
                                        border_width=2, height=58, corner_radius=0,
                                        command=self.save_weight)
        self.action_btn.pack(fill="x", padx=PAD)

        self.msg_label = ctk.CTkLabel(self, text="", font=FONT_SMALL, text_color=ACCENT)
        self.msg_label.pack(pady=8)

        ctk.CTkLabel(self, text="────────────────────────────────",
                     font=FONT_SMALL, text_color=BORDER).pack(pady=(12, 20))

        for text, cmd in [
            ("// ESTADÍSTICAS →",       on_stats),
            ("// NUEVA FASE →",         on_phase),
            ("// AÑADIR INFORME →",     on_report),
            ("// INFORME PARA IA →",    self._generate_ai_report),
        ]:
            ctk.CTkButton(self, text=text, font=FONT_LABEL,
                          fg_color=CARD, text_color=TEXT,
                          border_color=BORDER, border_width=1,
                          hover_color=HOVER_SEC, height=56, corner_radius=0,
                          command=cmd).pack(fill="x", padx=PAD, pady=(0, 10))

        ctk.CTkFrame(self, fg_color=BG, height=0).pack(expand=True)

        ctk.CTkLabel(self, text="────────────────────────────────",
                     font=FONT_SMALL, text_color=BORDER).pack(pady=(0, 6))
        ctk.CTkLabel(self, text="sergio / weights v0.1",
                     font=FONT_TINY, text_color=TEXT_DIM).pack(pady=(0, 24))

        self.check_today()

    def _generate_ai_report(self):
        import tkinter.filedialog as fd
        import tkinter.messagebox as mb

        path = fd.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Texto", "*.txt")],
            initialfile=f"informe_weights_{datetime.now().strftime('%Y%m%d')}.txt",
            title="Guardar informe para IA"
        )
        if path:
            text = generate_report()
            with open(path, "w", encoding="utf-8") as f:
                f.write(text)
            mb.showinfo("Informe generado", f"Guardado en:\n{path}")

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
            self.msg_label.configure(text="✗  introduce un peso", text_color="#ff4444"); return
        try:
            value = float(raw)
        except ValueError:
            self.msg_label.configure(text="✗  valor no válido", text_color="#ff4444"); return
        result = add_weight(value)
        self.msg_label.configure(
            text="✓  peso actualizado" if result == "updated" else "✓  peso añadido",
            text_color=ACCENT)
        self.weight_entry.delete(0, "end")
        self.check_today()


# ── Vista: Menú Estadísticas ──────────────────────────────────────────────────
class StatsMenuView(ctk.CTkFrame):
    def __init__(self, master, on_back, on_weight_stats, on_phase, on_reports):
        super().__init__(master, fg_color=BG)

        ctk.CTkLabel(self, text="// ESTADÍSTICAS", font=FONT_TITLE,
                     text_color=ACCENT).pack(pady=(44, 0))
        ctk.CTkLabel(self, text="────────────────────────────────",
                     font=FONT_SMALL, text_color=BORDER).pack(pady=(8, 40))

        for text, cmd in [
            ("// EVOLUCIÓN DE PESO →", on_weight_stats),
            ("// FASE ACTUAL →",       on_phase),
            ("// INFORMES →",          on_reports),
        ]:
            ctk.CTkButton(self, text=text, font=FONT_LABEL,
                          fg_color=CARD, text_color=TEXT,
                          border_color=BORDER, border_width=1,
                          hover_color=HOVER_SEC, height=60, corner_radius=0,
                          command=cmd).pack(fill="x", padx=PAD, pady=(0, 12))

        ctk.CTkLabel(self, text="────────────────────────────────",
                     font=FONT_SMALL, text_color=BORDER).pack(pady=(28, 8))
        ctk.CTkButton(self, text="← VOLVER AL MENÚ", font=FONT_SMALL,
                      fg_color="transparent", text_color=TEXT_DIM,
                      hover_color=HOVER_SEC, height=40, corner_radius=0,
                      command=on_back).pack()


# ── Vista: Fase Actual ────────────────────────────────────────────────────────
class CurrentPhaseView(ctk.CTkFrame):
    def __init__(self, master, on_back):
        super().__init__(master, fg_color=BG)

        header = ctk.CTkFrame(self, fg_color=BG)
        header.pack(fill="x", padx=PAD, pady=(36, 0))
        ctk.CTkButton(header, text="← VOLVER", font=FONT_SMALL,
                      fg_color="transparent", text_color=TEXT_DIM,
                      hover_color=HOVER_SEC, width=90, height=32,
                      corner_radius=0, command=on_back).pack(side="left")
        ctk.CTkLabel(header, text="// FASE ACTUAL", font=FONT_TITLE,
                     text_color=ACCENT).pack(side="left", padx=16)

        ctk.CTkLabel(self, text="────────────────────────────────",
                     font=FONT_SMALL, text_color=BORDER).pack(pady=(10, 24))

        phases = read_csv(PHASES_CSV_PATH)
        active = None
        for p in reversed(phases):
            if not p.get("end_date", "").strip():
                active = p; break

        if not active:
            ctk.CTkLabel(self, text="no hay fase activa", font=FONT_SMALL,
                         text_color=TEXT_DIM).pack(expand=True)
            return

        phase_type  = active.get("phase_type", "—")
        weight_goal = active.get("weight_goal", "")
        date_goal   = active.get("date_goal", "")
        start_date  = active.get("start_date", "")

        current_weight = get_today_weight()
        all_w          = get_weights_filtered("phase", start_date)
        start_weight   = all_w[0]["weight"] if all_w else None

        try:   w_goal  = float(weight_goal)
        except: w_goal = None
        try:   d_goal  = datetime.strptime(date_goal, "%d/%m/%y")
        except: d_goal = None
        try:   d_start = datetime.strptime(start_date, "%d/%m/%y")
        except: d_start = None

        type_colors = {"bulk": "#4a9eff", "cut": "#ff6b35", "maintenance": ACCENT}
        phase_color = type_colors.get(phase_type.lower(), ACCENT)

        type_card = ctk.CTkFrame(self, fg_color=CARD, corner_radius=0)
        type_card.pack(fill="x", padx=PAD, pady=(0, 16))
        ctk.CTkLabel(type_card, text="TIPO DE FASE", font=FONT_TINY,
                     text_color=TEXT_DIM).pack(anchor="w", padx=20, pady=(14, 2))
        ctk.CTkLabel(type_card, text=phase_type.upper(),
                     font=("Courier New", 34, "bold"),
                     text_color=phase_color).pack(anchor="w", padx=20, pady=(0, 14))

        grid = ctk.CTkFrame(self, fg_color=BG)
        grid.pack(fill="x", padx=PAD, pady=(0, 16))
        grid.columnconfigure(0, weight=1)
        grid.columnconfigure(1, weight=1)

        def metric_card(parent, row, col, label, value_text, value_color, sub_text=None, sub_color=TEXT_DIM):
            card = ctk.CTkFrame(parent, fg_color=CARD, corner_radius=0)
            card.grid(row=row, column=col, sticky="nsew", padx=(0 if col==0 else 6), pady=(0, 6))
            ctk.CTkLabel(card, text=label, font=FONT_TINY,
                         text_color=TEXT_DIM).pack(anchor="w", padx=16, pady=(14, 2))
            ctk.CTkLabel(card, text=value_text, font=("Courier New", 26, "bold"),
                         text_color=value_color).pack(anchor="w", padx=16)
            ctk.CTkLabel(card, text=sub_text or "", font=FONT_SMALL,
                         text_color=sub_color).pack(anchor="w", padx=16, pady=(2, 14))

        w_cur_txt  = f"{current_weight:.2f} kg" if current_weight else "—"
        w_goal_txt = f"{w_goal:.2f} kg" if w_goal else "—"
        metric_card(grid, 0, 0, "PESO ACTUAL",   w_cur_txt,  ACCENT)
        metric_card(grid, 0, 1, "PESO OBJETIVO", w_goal_txt, ACCENT)

        if current_weight and w_goal:
            diff = w_goal - current_weight
            metric_card(grid, 1, 0, "DIFERENCIA CON OBJETIVO",
                        f"{'+'if diff>0 else ''}{diff:.2f} kg", ACCENT, "para llegar al objetivo")
        else:
            metric_card(grid, 1, 0, "DIFERENCIA CON OBJETIVO", "—", TEXT_DIM)

        if current_weight and start_weight:
            gained = current_weight - start_weight
            is_bulk = phase_type.lower() == "bulk"
            is_cut  = phase_type.lower() == "cut"
            if is_bulk:   prog_color = "#4caf50" if gained > 0 else "#f44336"
            elif is_cut:  prog_color = "#4caf50" if gained < 0 else "#f44336"
            else:         prog_color = ACCENT
            metric_card(grid, 1, 1, "DESDE INICIO DE FASE",
                        f"{'+'if gained>0 else ''}{gained:.2f} kg", prog_color,
                        f"inicio: {start_weight:.2f} kg")
        else:
            metric_card(grid, 1, 1, "DESDE INICIO DE FASE", "—", TEXT_DIM)

        if d_goal:
            days_left = (d_goal - datetime.now()).days
            days_txt  = f"{days_left} días" if days_left >= 0 else f"{abs(days_left)} días pasados"
            metric_card(grid, 2, 0, "FECHA OBJETIVO", d_goal.strftime("%d/%m/%Y"), ACCENT)
            metric_card(grid, 2, 1, "DÍAS RESTANTES", days_txt, ACCENT)
        else:
            metric_card(grid, 2, 0, "FECHA OBJETIVO", "—", TEXT_DIM)
            metric_card(grid, 2, 1, "DÍAS RESTANTES", "—", TEXT_DIM)

        if d_start:
            elapsed = (datetime.now() - d_start).days
            metric_card(grid, 3, 0, "DÍAS EN FASE", f"{elapsed} días", ACCENT,
                        f"desde {d_start.strftime('%d/%m/%Y')}")
        else:
            metric_card(grid, 3, 0, "DÍAS EN FASE", "—", TEXT_DIM)

        if d_start and d_goal:
            total_days   = (d_goal - d_start).days
            elapsed_days = (datetime.now() - d_start).days
            pct = max(0, min(1, elapsed_days / total_days)) if total_days > 0 else 0
            metric_card(grid, 3, 1, "PROGRESO TEMPORAL", f"{pct*100:.0f}%", ACCENT,
                        f"{elapsed_days} de {total_days} días")

            bar_frame = ctk.CTkFrame(self, fg_color=CARD, corner_radius=0)
            bar_frame.pack(fill="x", padx=PAD, pady=(0, 16))
            ctk.CTkLabel(bar_frame, text="PROGRESO DE FASE", font=FONT_TINY,
                         text_color=TEXT_DIM).pack(anchor="w", padx=16, pady=(14, 6))
            pb = ctk.CTkProgressBar(bar_frame, progress_color=ACCENT,
                                    fg_color=BORDER, height=14, corner_radius=0)
            pb.pack(fill="x", padx=16, pady=(0, 14))
            pb.set(pct)


# ── Vista: Informes nutricionista ─────────────────────────────────────────────
class NutritionistReportsView(ctk.CTkFrame):
    def __init__(self, master, on_back):
        super().__init__(master, fg_color=BG)

        header = ctk.CTkFrame(self, fg_color=BG)
        header.pack(fill="x", padx=PAD, pady=(36, 0))
        ctk.CTkButton(header, text="← VOLVER", font=FONT_SMALL,
                      fg_color="transparent", text_color=TEXT_DIM,
                      hover_color=HOVER_SEC, width=90, height=32,
                      corner_radius=0, command=on_back).pack(side="left")
        ctk.CTkLabel(header, text="// INFORMES", font=FONT_TITLE,
                     text_color=ACCENT).pack(side="left", padx=16)

        ctk.CTkLabel(self, text="────────────────────────────────",
                     font=FONT_SMALL, text_color=BORDER).pack(pady=(10, 16))

        REPORTS_CSV_PATH = os.path.join(BASE_DIR, "data", "reports.csv")
        reports = read_csv(REPORTS_CSV_PATH)

        if not reports:
            ctk.CTkLabel(self, text="no hay informes registrados", font=FONT_SMALL,
                         text_color=TEXT_DIM).pack(expand=True)
            return

        METRICS = [
            ("body_fat_pct",         "% GRASA",         False),
            ("skeletal_muscle_mass", "M.M. ESQ.",        True),
            ("fat_free_mass",        "M. LIBRE GRASA",   True),
            ("visceral_fat_index",   "GRASA VISCERAL",   False),
            ("muscle_quality",       "CAL. MUSCULAR",    True),
            ("trunk_fat_kg",         "TRONCO kg",        False),
            ("trunk_fat_pct",        "TRONCO %",         False),
            ("total_body_water",     "AGUA CORP.",       True),
            ("neck_cm",              "CUELLO cm",        None),
            ("chest_cm",             "PECHO cm",         None),
            ("bicep_cm",             "BÍCEP cm",         True),
            ("hip_cm",               "CADERA cm",        None),
            ("thigh_cm",             "MUSLO cm",         True),
        ]

        scroll = ctk.CTkScrollableFrame(self, fg_color=BG)
        scroll.pack(fill="both", expand=True, padx=PAD, pady=(0, 16))

        n = len(reports)
        total_cols = 1 + n + (n - 1)
        scroll.grid_columnconfigure(0, weight=2, minsize=140)
        for i in range(1, total_cols):
            scroll.grid_columnconfigure(i, weight=1, minsize=72)

        ctk.CTkLabel(scroll, text="", font=FONT_TINY, fg_color=CARD).grid(
            row=0, column=0, sticky="nsew", padx=(0,2), pady=(0,2))
        col = 1
        for i, r in enumerate(reports):
            ctk.CTkLabel(scroll, text=r.get("date","—"), font=FONT_TINY,
                         text_color=ACCENT, fg_color=CARD, anchor="center").grid(
                row=0, column=col, sticky="nsew", padx=(0,2), pady=(0,2), ipady=10)
            col += 1
            if i < n - 1:
                ctk.CTkLabel(scroll, text="Δ", font=FONT_TINY, text_color=TEXT_DIM,
                             fg_color=BG, anchor="center").grid(
                    row=0, column=col, sticky="nsew", padx=(0,2), pady=(0,2))
                col += 1

        for row_idx, (key, label, up_is_good) in enumerate(METRICS, start=1):
            bg_row = CARD if row_idx % 2 == 0 else "#0f0f0f"
            ctk.CTkLabel(scroll, text=label, font=FONT_TINY, text_color=TEXT_DIM,
                         fg_color=bg_row, anchor="w").grid(
                row=row_idx, column=0, sticky="nsew", padx=(0,2), pady=(0,1), ipady=9, ipadx=8)
            col = 1
            for i, r in enumerate(reports):
                raw = r.get(key, "")
                try:    val = float(raw); val_txt = f"{val:.1f}"
                except: val = None;       val_txt = "—"

                ctk.CTkLabel(scroll, text=val_txt, font=FONT_TINY, text_color=TEXT,
                             fg_color=bg_row, anchor="center").grid(
                    row=row_idx, column=col, sticky="nsew", padx=(0,2), pady=(0,1), ipady=9)
                col += 1

                if i < n - 1:
                    try:
                        nv    = float(reports[i+1].get(key, ""))
                        delta = nv - val
                        dtxt  = f"{'+'if delta>0 else ''}{delta:.1f}"
                        if up_is_good is None:                                     dc = TEXT_DIM
                        elif (delta>0 and up_is_good) or (delta<0 and not up_is_good): dc = "#4caf50"
                        elif delta == 0:                                            dc = TEXT_DIM
                        else:                                                       dc = "#f44336"
                    except: dtxt = "—"; dc = TEXT_DIM

                    ctk.CTkLabel(scroll, text=dtxt, font=("Courier New", 12, "bold"),
                                 text_color=dc, fg_color=BG, anchor="center").grid(
                        row=row_idx, column=col, sticky="nsew", padx=(0,2), pady=(0,1), ipady=9)
                    col += 1


# ── App principal ─────────────────────────────────────────────────────────────
class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("WEIGHTS")
        
        icon_path = os.path.join(BASE_DIR, "icon.icns")
        if os.path.exists(icon_path):
            img = Image.open(icon_path)
            photo = ImageTk.PhotoImage(img)
            self.iconphoto(True, photo)

        self.configure(fg_color=BG)
        self.resizable(False, False)
        # Centrar en pantalla
        w, h = 980, 980
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")
        self.show_home()

    def show_home(self):
        self._clear()
        HomeView(self, on_phase=self.show_phase,
                 on_report=self.show_report,
                 on_stats=self.show_stats).pack(fill="both", expand=True)

    def show_phase(self):
        self._clear()
        PhaseView(self, on_back=self.show_home).pack(fill="both", expand=True)

    def show_report(self):
        self._clear()
        ReportView(self, on_back=self.show_home).pack(fill="both", expand=True)

    def show_stats(self):
        self._clear()
        StatsMenuView(self,
                      on_back=self.show_home,
                      on_weight_stats=lambda: (self._clear(), StatsView(self, on_back=self.show_stats).pack(fill="both", expand=True)),
                      on_phase=lambda: (self._clear(), CurrentPhaseView(self, on_back=self.show_stats).pack(fill="both", expand=True)),
                      on_reports=lambda: (self._clear(), NutritionistReportsView(self, on_back=self.show_stats).pack(fill="both", expand=True))
                      ).pack(fill="both", expand=True)

    def _clear(self):
        for widget in self.winfo_children():
            widget.destroy()


if __name__ == "__main__":
    app = App()
    app.mainloop()
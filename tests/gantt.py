"""
Generador de Diagrama de Gantt
==============================
Uso:
  1. Edita la lista TAREAS con tus tareas y fechas.
  2. Ejecuta: python gantt.py
  3. Se guardará un archivo "gantt.png" en el mismo directorio.

Dependencias:
  pip install matplotlib
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.dates import DateFormatter, MonthLocator
from datetime import datetime

# ─────────────────────────────────────────────
#  CONFIGURA TU PROYECTO AQUÍ
# ─────────────────────────────────────────────

TITULO_PROYECTO = "Mi Proyecto"

# Formato de fechas: "DD/MM/YYYY"
TAREAS = [
    {"nombre": "Especificación de Requisitos", "inicio": "16/12/2024", "fin": "31/01/2025", "categoria": "Planificación"},
    {"nombre": "Análisis e Investigación",     "inicio": "20/12/2024", "fin": "25/07/2025", "categoria": "Investigación"},
    {"nombre": "Diseño de la Solución",        "inicio": "07/03/2025", "fin": "02/05/2025", "categoria": "Diseño"},
    {"nombre": "Implementación",               "inicio": "02/05/2025", "fin": "17/10/2025", "categoria": "Implementación"},
    {"nombre": "Pruebas y Correcciones",       "inicio": "17/10/2025", "fin": "27/02/2026", "categoria": "Pruebas"},
    {"nombre": "Análisis de Resultados",       "inicio": "23/01/2026", "fin": "06/03/2026", "categoria": "Análisis de resultados"},
    {"nombre": "Redacción de la Memoria",      "inicio": "06/03/2026", "fin": "15/05/2026", "categoria": "Memoria"},
]

# ─────────────────────────────────────────────
#  PALETA DE COLORES POR CATEGORÍA
#  Añade nuevas categorías aquí si las necesitas
# ─────────────────────────────────────────────

COLORES = {
    "Planificación":          "#4E9AF1",
    "Investigación":          "#8A7BDB",
    "Diseño":                 "#F1A74E",
    "Implementación":         "#4EBF8A",
    "Pruebas":                "#C97BDB",
    "Análisis de resultados": "#DB7BA4",
    "Memoria":                "#E05C5C",
}
COLOR_DEFECTO = "#888888"  # Para categorías no definidas arriba

# ─────────────────────────────────────────────
#  GENERACIÓN DEL GRÁFICO (no editar)
# ─────────────────────────────────────────────

def color_para(categoria):
    return COLORES.get(categoria, COLOR_DEFECTO)

def parse(fecha_str):
    return datetime.strptime(fecha_str, "%d/%m/%Y")

def generar_gantt():
    fig, ax = plt.subplots(figsize=(14, len(TAREAS) * 0.7 + 2.5))
    fig.patch.set_facecolor("#FFFFFF")
    ax.set_facecolor("#FFFFFF")

    fechas_inicio = [parse(t["inicio"]) for t in TAREAS]
    fechas_fin    = [parse(t["fin"])    for t in TAREAS]
    nombres       = [t["nombre"]        for t in TAREAS]
    categorias    = [t["categoria"]     for t in TAREAS]

    n = len(TAREAS)
    altura_barra = 0.55
    y_positions  = list(range(n))

    for i, tarea in enumerate(TAREAS):
        inicio   = parse(tarea["inicio"])
        fin      = parse(tarea["fin"])
        color    = color_para(tarea["categoria"])
        duracion = fin - inicio

        # Barra principal
        ax.barh(
            i,
            duracion.days,
            left=inicio,
            height=altura_barra,
            color=color,
            alpha=0.88,
            zorder=3,
            edgecolor="white",
            linewidth=0.4,
        )

        # Etiqueta dentro/fuera de la barra
        #cx = inicio + duracion / 2
        #ax.text(
        #    cx, i,
        #    f"  {duracion.days}d  ",
        #    va="center", ha="center",
        #    fontsize=11, color="white",
        #    fontweight="bold", zorder=4,
        #)

    # Línea del día actual
    #hoy = datetime.today()
    #if fechas_inicio[0] <= hoy <= fechas_fin[-1]:
    #    ax.axvline(hoy, color="#FFD700", linewidth=1.5, linestyle="--", zorder=5, label="Hoy")
    #    ax.text(hoy, n - 0.1, "  hoy", color="#FFD700", fontsize=8, va="top", zorder=6)

    # Cuadrícula
    #ax.xaxis.set_major_locator(WeekdayLocator(byweekday=MO))
    #ax.xaxis.set_major_formatter(DateFormatter("%d %b"))
    ax.xaxis.set_major_locator(MonthLocator(interval=2))
    ax.xaxis.set_major_formatter(DateFormatter("%b %Y"))
    #plt.xticks(rotation=35, ha="right", color="#111111", fontsize=8)
    plt.xticks(rotation=35, ha="right", color="#111111", fontsize=14)

    # Eje Y — nombres de tareas
    ax.set_yticks(y_positions)
    #ax.set_yticklabels(nombres, color="#111111", fontsize=9.5)
    ax.set_yticklabels(nombres, color="#111111", fontsize=13)
    ax.invert_yaxis()

    # Bordes y grid
    for spine in ax.spines.values():
        spine.set_edgecolor("#CCCCCC")
    ax.grid(axis="x", color="#DDDDDD", linestyle="--", linewidth=0.6, zorder=0)
    ax.tick_params(colors="#111111")

    # Título
    #ax.set_title(
    #    TITULO_PROYECTO,
    #    fontsize=16, fontweight="bold",
    #    color="white", pad=16,
    #)

    # Leyenda de categorías
    categorias_unicas = list(dict.fromkeys(categorias))
    parches = [
        mpatches.Patch(color=color_para(c), label=c)
        for c in categorias_unicas
    ]
    ax.legend(
        handles=parches,
        loc="upper right",
        framealpha=0.8,
        labelcolor="black",
        fontsize=13,
        edgecolor="#CCCCCC",
    )

    plt.tight_layout()
    output = "gantt.pdf"
    #plt.savefig(output, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.savefig(
        output,
        format="pdf",
        dpi=600,
        bbox_inches="tight"
    )
    #print(f"✅ Diagrama guardado como '{output}'")
    plt.show()

if __name__ == "__main__":
    generar_gantt()
import json
import csv
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

from pathlib import Path
from collections import defaultdict
from scipy import stats

# ============================================================
# CONFIGURACIÓN VISUAL  (ajusta a tu gusto)
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

NETWORKS        = ["Abilene", "Geant", "Nobel", "Germany"]
STRATEGIES      = ["normal", "vch"]
PSO_CONFIGS     = ["100p_600i",  "200p_600i",  "100p_1200i", "200p_1200i"]
CONFIG_LABELS   = ["100p · 600i", "200p · 600i", "100p · 1200i", "200p · 1200i"]

COLORS = {
    "normal": "#2980B9", # Azul
    "vch":    "#85C1E9", # Azul claro
}
STRATEGY_LABELS = {
    "normal": "PSO Normal",
    "vch":    "PSO VCH",
}

# Tipografía / tamaño de figura
fuente         = 12
fuente_eje     = 13
fuente_leyenda = 11
fs             = (10, 5)


# ============================================================
# UTILIDADES
# ============================================================

def confidence_interval(values: list[float], confidence: float = 0.95):
    """Devuelve (media, semi-amplitud del IC) usando t de Student."""
    n    = len(values)
    mean = np.mean(values)
    if n < 2:
        return mean, 0.0
    se  = stats.sem(values)
    h   = se * stats.t.ppf((1 + confidence) / 2, df=n - 1)
    return mean, h


def load_csv(csv_path: Path) -> dict:
    """
    Lee benchmark_times.csv y devuelve un dict:
        data[network][strategy][pso_config] = [time_s, ...]
    Solo incluye filas sin error.
    """
    data = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))

    with open(csv_path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["time_s"] == "ERROR":
                continue
            data[row["network"]][row["strategy"]][row["pso_config"]].append(
                float(row["time_s"])
            )

    return data


# ============================================================
# FUNCIÓN PRINCIPAL
# ============================================================

def plot_topology_time_bars(
    csv_path: str | Path = None,
    confidence: float = 0.95,
    output_dir: str | Path = None,
    fmt: str = "pdf",
    show: bool = True,
):
    """
    Genera y guarda una gráfica de barras agrupadas por cada topología de red.

    Parámetros
    ----------
    csv_path   : ruta al CSV generado por benchmark_pso.py.
                 Por defecto: <PROJECT_ROOT>/results/benchmark_times.csv
    confidence : nivel de confianza para el IC (default 0.95).
    output_dir : carpeta donde se guardan las figuras.
                 Por defecto: <PROJECT_ROOT>/results/figures/
    fmt        : formato de salida — "pdf", "png", "svg" …
    show       : si True llama a plt.show() tras cada figura.
    """

    csv_path   = Path(csv_path)   if csv_path   else PROJECT_ROOT / "results" / "benchmark_times.csv"
    output_dir = Path(output_dir) if output_dir else PROJECT_ROOT / "results" / "figures"
    output_dir.mkdir(parents=True, exist_ok=True)

    data = load_csv(csv_path)

    n_configs    = len(PSO_CONFIGS)
    n_strategies = len(STRATEGIES)
    bar_width    = 0.35                          # ancho de cada barra
    group_gap    = 0.1                           # separación extra entre grupos de config
    offsets      = np.array([-bar_width / 2, bar_width / 2])

    # Posición central de cada grupo de configuración
    group_centers = np.arange(n_configs) * (bar_width * n_strategies + group_gap + 0.1)

    plt.rcParams.update({
        "font.size":        fuente,
        "axes.labelsize":   fuente_eje,
        "legend.fontsize":  fuente_leyenda,
    })

    for network in NETWORKS:
        if network not in data:
            print(f"[AVISO] {network} no encontrada en el CSV, se omite.")
            continue

        fig, ax = plt.subplots(figsize=fs)

        for s_idx, strategy in enumerate(STRATEGIES):
            means  = []
            errors = []

            for cfg in PSO_CONFIGS:
                times = data[network][strategy].get(cfg, [])

                if len(times) < 2:
                    print(f"  [AVISO] {network} | {strategy} | {cfg}: "
                          f"solo {len(times)} valores, IC no calculable.")
                    means.append(np.mean(times) if times else 0.0)
                    errors.append(0.0)
                else:
                    mean, ci = confidence_interval(times, confidence)
                    means.append(mean)
                    errors.append(ci)

            x_positions = group_centers + offsets[s_idx]

            ax.bar(
                x_positions,
                means,
                width=bar_width,
                yerr=errors,
                capsize=5,
                color=COLORS[strategy],
                label=STRATEGY_LABELS[strategy],
                alpha=0.88,
                error_kw={"elinewidth": 1.4, "ecolor": "black"},
            )

        # Ejes y etiquetas
        ax.set_xticks(group_centers)
        ax.set_xticklabels(CONFIG_LABELS, fontsize=fuente)
        ax.set_ylabel("Tiempo de ejecución (s)", fontsize=fuente_eje)
        #ax.set_title(f"Tiempos PSO — {network}", fontsize=fuente + 1, fontweight="bold")
        ax.legend(loc="upper left", framealpha=0.85)
        ax.grid(axis="y", linestyle="--", alpha=0.55)
        ax.set_axisbelow(True)

        fig.tight_layout()

        filename = f"times_{network}.{fmt}"
        filepath = output_dir / filename
        fig.savefig(filepath, format=fmt, dpi=600, bbox_inches="tight")
        print(f"  Guardada: {filepath}")

        if show:
            plt.show()

        plt.close(fig)

    print(f"\nFiguras guardadas en: {output_dir}")


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Grafica tiempos del benchmark PSO")
    parser.add_argument("--csv",        default=None,  help="Ruta al CSV de benchmark")
    parser.add_argument("--output",     default=None,  help="Carpeta de salida de figuras")
    parser.add_argument("--confidence", default=0.95,  type=float, help="Nivel de confianza IC")
    parser.add_argument("--fmt",        default="pdf", help="Formato de figura: pdf, png, svg …")
    parser.add_argument("--no-show",    action="store_true", help="No llamar a plt.show()")
    args = parser.parse_args()

    plot_topology_time_bars(
        csv_path   = args.csv,
        confidence = args.confidence,
        output_dir = args.output,
        fmt        = args.fmt,
        show       = not args.no_show,
    )
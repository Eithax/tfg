import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# ============================================================
# DATOS
# ============================================================

MAX_CARBON = {
    "Abilene": {
        1: 119.23285957325584,
        2: 120.1275744665698,
        3: 122.49521077433485,
        4: 124.44984242414479,
        5: 125.42715824904977
    },
    "Geant": {
        1: 243.43302882243873,
        2: 244.4690691882402,
        3: 245.2932219294174,
        4: 246.12476584315752,
        5: 247.10510576733463
    },
    "Nobel": {
        1: 274.5541053459976,
        2: 275.5825264151971,
        3: 277.1251580189963,
        4: 279.69621069199496,
        5: 284.83831603799234
    },
    "Germany": {
        1: 902.0110059173542,
        2: 904.8737573966937,
        3: 910.5992603553727,
        4: 916.3247633140517,
        5: 919.1875147933912
    }
}

PROJECT_ROOT = Path(__file__).resolve().parents[1]

# Tipografía / tamaño de figura
fuente       = 12
fuente_eje   = 13
fs           = (7, 4)


# ============================================================
# FUNCIÓN PRINCIPAL
# ============================================================

def plot_max_carbon_bars(
    data: dict = None,
    output_dir: str | Path = None,
    fmt: str = "pdf",
    show: bool = True,
):
    """
    Genera y guarda una gráfica de barras por topología con los valores
    de MAX_CARBON para cada matriz de tráfico.

    Parámetros
    ----------
    data       : dict con la estructura MAX_CARBON.
                 Por defecto usa el dict definido en este módulo.
    output_dir : carpeta donde se guardan las figuras.
                 Por defecto: <PROJECT_ROOT>/results/figures/
    fmt        : formato de salida — "pdf", "png", "svg" …
    show       : si True llama a plt.show() tras cada figura.
    """

    data       = data       or MAX_CARBON
    output_dir = Path(output_dir) if output_dir else PROJECT_ROOT / "results" / "figures"
    output_dir.mkdir(parents=True, exist_ok=True)

    plt.rcParams.update({
        "font.size":      fuente,
        "axes.labelsize": fuente_eje,
    })

    for network, tm_values in data.items():
        labels = [f"TM{tm}" for tm in tm_values]
        values = list(tm_values.values())

        fig, ax = plt.subplots(figsize=fs)

        ax.bar(labels, values, color="#E67E22", alpha=0.88)

        ax.set_ylabel("Emisiones (gCO₂)", fontsize=fuente_eje)
        #ax.set_title(f"Carbono máximo — {network}", fontsize=fuente + 1, fontweight="bold")
        ax.grid(axis="y", linestyle="--", alpha=0.55)
        ax.set_axisbelow(True)

        # Margen vertical para que las barras no toquen el borde superior
        ax.set_ylim(min(values) * 0.995, max(values) * 1.005)

        fig.tight_layout()

        filepath = output_dir / f"max_carbon_{network}.{fmt}"
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

    parser = argparse.ArgumentParser(description="Grafica MAX_CARBON por topología")
    parser.add_argument("--output", default=None,  help="Carpeta de salida")
    parser.add_argument("--fmt",    default="pdf", help="Formato: pdf, png, svg …")
    parser.add_argument("--no-show", action="store_true", help="No llamar a plt.show()")
    args = parser.parse_args()

    plot_max_carbon_bars(
        output_dir = args.output,
        fmt        = args.fmt,
        show       = not args.no_show,
    )
import os
import re
import json
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from collections import defaultdict
from libs.utils import confidence_interval, parse_config_dir

PROJECT_ROOT = Path(__file__).resolve().parents[1]
fuente = 14
fuente_eje = 11
fuente_leyenda = fuente-5
fs = (6, 4)

def plot_from_json(files, title="Evolución del coste por iteración"):
    """Dibuja las curvas de coste de uno o varios ficheros de resultados JSON."""
    plt.figure(figsize=(10, 6))
    for file_path in files:
        with open(file_path, "r") as f:
            data = json.load(f)

        network = data.get("network", "Unknown")
        tm = data.get("traffic_matrix", "TM?")
        threads = data.get("config", {}).get("threads", "?")

        for run_data in data.get("results", []):
            cost_history = run_data.get("cost_history", [])

            if isinstance(cost_history, dict) and "data" in cost_history:
                xs = [p["iter"] for p in cost_history["data"]]
                ys = [p["cost"] if p["cost"] is not None else np.nan for p in cost_history["data"]]
            elif isinstance(cost_history, list):
                xs = list(range(1, len(cost_history) + 1))
                ys = [y if np.isfinite(y) else np.nan for y in cost_history]
            else:
                continue

            label = f"{network}-TM{tm}-T{threads}-Run{run_data.get('run', '?')}"
            plt.plot(xs, ys, label=label)

    plt.xlabel("Iteración")
    plt.ylabel("Coste")
    plt.title(title)
    plt.legend(fontsize=8)
    plt.grid(True)
    plt.tight_layout()
    plt.show()


def plot_avg_cost_histories(files, title="Coste promedio por iteración"):
    """Dibuja la media y desviación estándar del coste a lo largo de las iteraciones."""
    plt.figure(figsize=(10, 6))

    for file_path in files:
        with open(file_path, "r") as f:
            data = json.load(f)

        network = data.get("network", "Unknown")
        tm = data.get("traffic_matrix", "?")
        threads = data.get("config", {}).get("threads", "?")

        histories = []
        for run_data in data.get("results", []):
            cost_history = run_data.get("cost_history", [])
            if isinstance(cost_history, dict) and "data" in cost_history:
                ys = [p["cost"] if p["cost"] is not None else np.nan for p in cost_history["data"]]
            elif isinstance(cost_history, list):
                ys = [y if np.isfinite(y) else np.nan for y in cost_history]
            else:
                continue
            histories.append(ys)

        if not histories:
            continue

        min_len = min(len(h) for h in histories)
        histories = [h[:min_len] for h in histories]
        arr = np.array(histories)
        mean = np.nanmean(arr, axis=0)
        std = np.nanstd(arr, axis=0)

        xs = list(range(1, len(mean) + 1))
        label = f"{network}-TM{tm}-T{threads}"
        plt.plot(xs, mean, label=label)
        plt.fill_between(xs, mean - std, mean + std, alpha=0.2)

    plt.xlabel("Iteración")
    plt.ylabel("Coste promedio ± desviación")
    plt.title(title)
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()



"""
    Dibuja la evolución del coste (gCO₂/kWh) frente a las iteraciones
    para una matriz de tráfico concreta (TM).

    Parámetros:
        files: lista de rutas a ficheros JSON
        tm_target: número o nombre de la matriz de tráfico a mostrar (p. ej. 1 o "AbileneTM1")
        group_by: 'config' agrupa por parámetros PSO (c1, c2, w, k),
                  'threads' agrupa por número de hilos
    """
def plot_cost_vs_iterations(files, tm_target=None, group_by="config"):
    plt.figure(figsize=(10, 6))

    for file_path in files:
        file = Path(file_path)
        with open(file, "r") as f:
            data = json.load(f)

        tm = str(data.get("traffic_matrix", ""))
        if tm_target and str(tm_target) not in tm:
            continue  # saltamos si no coincide la TM que queremos

        network = data.get("network", "Unknown")
        cfg = data.get("config", {})

        label = f"{network}"
        if group_by == "config":
            label += f" | c1={cfg.get('c1')} c2={cfg.get('c2')} w={cfg.get('w')} k={cfg.get('k')}"
        elif group_by == "threads":
            label += f" | {cfg.get('threads')} threads"

        # Calcular coste promedio por iteración (por si hay varias runs)
        all_histories = []
        for run in data.get("results", []):
            hist = run.get("cost_history", {})
            if isinstance(hist, dict) and "data" in hist:
                costs = [p["cost"] if p["cost"] is not None else np.nan for p in hist["data"]]
            elif isinstance(hist, list):
                costs = [c if np.isfinite(c) else np.nan for c in hist]
            else:
                continue
            all_histories.append(costs)

        if not all_histories:
            continue

        min_len = min(len(h) for h in all_histories)
        arr = np.array([h[:min_len] for h in all_histories])
        mean = np.nanmean(arr, axis=0)

        plt.plot(range(1, len(mean) + 1), mean, label=label)

    plt.title(f"Coste medio por iteración — TM {tm_target or 'todas'}")
    plt.xlabel("Iteraciones")
    plt.ylabel("Coste (gCO₂/kWh)")
    plt.legend(fontsize=8)
    plt.grid(True)
    plt.tight_layout()
    plt.show()


"""
    Dibuja el coste final frente al número de partículas.

    Parámetros:
        files: lista de rutas a ficheros JSON
        tm_target: filtra una TM específica
        metric: métrica del eje Y ('best_cost' o 'mean_cost')
        group_by: cómo agrupar las líneas ('config', 'threads', etc.)
    """
def plot_cost_vs_particles(files, tm_target=None, metric="best_cost", group_by="config"):
    results = []

    # Extraer datos de todos los ficheros
    for file_path in files:
        with open(file_path, "r") as f:
            data = json.load(f)

        tm = str(data.get("traffic_matrix", ""))
        if tm_target and str(tm_target) not in tm:
            continue

        cfg = data.get("config", {})
        particles = cfg.get("particles")
        label_key = ""

        if group_by == "config":
            label_key = f"c1={cfg.get('c1')},c2={cfg.get('c2')},w={cfg.get('w')},k={cfg.get('k')}"
        elif group_by == "threads":
            label_key = f"{cfg.get('threads')} threads"
        else:
            label_key = "default"

        best_costs = [r.get("best_cost") for r in data.get("results", [])]
        avg_cost = np.nanmean(best_costs) if best_costs else np.nan
        results.append((label_key, particles, avg_cost))

    # Agrupar y pintar
    plt.figure(figsize=(10, 6))
    labels = sorted(set(r[0] for r in results))
    for label in labels:
        subset = sorted([r for r in results if r[0] == label], key=lambda x: x[1])
        xs = [r[1] for r in subset]
        ys = [r[2] for r in subset]
        plt.plot(xs, ys, marker="o", label=label)

    plt.title(f"Coste medio vs partículas — TM {tm_target or 'todas'}")
    plt.xlabel("Número de partículas")
    plt.ylabel("Coste medio (gCO₂/kWh)")
    plt.legend(fontsize=8)
    plt.grid(True)
    plt.tight_layout()
    plt.show()


"""
Calcula la media de best_cost y genera una gráfica
de coste medio vs número de iteraciones para cada combinación c1–c2.
"""
def procesar_barrido_iteraciones(
    network,
    pso_type,
    iter_start,
    iter_end,
    iter_step,
    particles_fixed,
    tm_index=1
):
    base_path = PROJECT_ROOT / "results" / network / pso_type

    resultados = defaultdict(dict)

    for config_dir in base_path.iterdir():
        if not config_dir.is_dir():
            continue

        # Ignorar sweep_figures u otros directorios
        if not config_dir.name.startswith("p"):
            continue

        particles, iterations, c1, c2, _, _ = parse_config_dir(config_dir.name)

        if particles != particles_fixed:
            continue

        if iterations < iter_start or iterations > iter_end:
            continue

        if (iterations - iter_start) % iter_step != 0:
            continue

        results_path = config_dir / f"TM{tm_index}" / "results.json"
        if not results_path.exists():
            continue

        with open(results_path) as f:
            data = json.load(f)

        costs = [
            r["best_cost"]
            for r in data["results"]
            if r["best_cost"] is not None
        ]

        if costs:
            mean_cost = sum(costs) / len(costs)
            resultados[(c1, c2)][iterations] = mean_cost

    # ---- Pintar ----
    plt.rcParams.update({
        "font.size": fuente,
        "axes.labelsize": fuente_eje,
        "legend.fontsize": fuente_leyenda
    })
    plt.figure(figsize=fs)

    for (c1, c2), valores in sorted(resultados.items()):
        xs = sorted(valores.keys())
        ys = [valores[x] for x in xs]
        plt.plot(xs, ys, marker="o", label=f"c1={c1}, c2={c2}")

    plt.title(f"{network} - {pso_type} - TM{tm_index}\nCoste medio vs Iteraciones (particulas={particles_fixed})")
    plt.xlabel("Iteraciones")
    plt.ylabel("Coste medio (gCO₂/kWh)")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()

    output_dir = (
            PROJECT_ROOT /
            "results" /
            network /
            pso_type /
            "sweep_figures"
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    filename = (
        f"iteraciones_{iter_start}-{iter_end}_"
        f"p{particles_fixed}.pdf"
    )
    plt.savefig(
        output_dir / filename,
        format="pdf",
        dpi=600,
        bbox_inches="tight"
    )

    plt.show()

    return resultados


"""
Calcula la media de best_cost y genera una gráfica
de coste medio vs número de iteraciones para cada combinación c1–c2.
Añade un sombreado a cada gráfica que representa el valor mínimo y máximo que
ha alcanzado a lo largo del barrido
"""
def procesar_barrido_iteraciones_min_max(
    network,
    pso_type,
    iter_start,
    iter_end,
    iter_step,
    particles_fixed,
    tm_index=1
):
    from pathlib import Path
    import json
    import matplotlib.pyplot as plt
    from collections import defaultdict

    base_path = PROJECT_ROOT / "results" / network / pso_type
    resultados = defaultdict(dict)

    for config_dir in base_path.iterdir():
        if not config_dir.is_dir():
            continue

        # Ignorar sweep_figures u otros directorios
        if not config_dir.name.startswith("p"):
            continue

        particles, iterations, c1, c2, _, _ = parse_config_dir(config_dir.name)

        if particles != particles_fixed:
            continue

        if iterations < iter_start or iterations > iter_end:
            continue

        if (iterations - iter_start) % iter_step != 0:
            continue

        results_path = config_dir / f"TM{tm_index}" / "results.json"
        if not results_path.exists():
            continue

        with open(results_path) as f:
            data = json.load(f)

        costs = [
            r["best_cost"]
            for r in data["results"]
            if r["best_cost"] is not None
        ]

        if costs:
            mean_cost = sum(costs) / len(costs)
            resultados[(c1, c2)][iterations] = {
                "mean": mean_cost,
                "min": min(costs),
                "max": max(costs)
            }

    # ---- Pintar ----
    plt.rcParams.update({
        "font.size": fuente,
        "axes.labelsize": fuente_eje,
        "legend.fontsize": fuente_leyenda
    })
    plt.figure(figsize=fs)

    for (c1, c2), valores in sorted(resultados.items()):
        xs = sorted(valores.keys())
        ys_mean = [valores[x]["mean"] for x in xs]
        ys_min = [valores[x]["min"] for x in xs]
        ys_max = [valores[x]["max"] for x in xs]

        plt.plot(xs, ys_mean, marker="o", label=f"c1={c1}, c2={c2}")
        plt.fill_between(xs, ys_min, ys_max, alpha=0.2)

    plt.title(f"{network} - {pso_type} - TM{tm_index}\nCoste medio ± rango vs Iteraciones (particulas={particles_fixed})")
    plt.xlabel("Iteraciones")
    plt.ylabel("Coste medio (gCO₂/kWh)")
    plt.legend(title="c1–c2")
    plt.grid(True)
    plt.tight_layout()

    output_dir = (
            PROJECT_ROOT /
            "results" /
            network /
            pso_type /
            "sweep_figures"
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    filename = (
        f"iteraciones_{iter_start}-{iter_end}_"
        f"p{particles_fixed}_minmax.pdf"
    )
    plt.savefig(
        output_dir / filename,
        format="pdf",
        dpi=600,
        bbox_inches="tight"
    )

    plt.show()

    return resultados


"""
Calcula la media de best_cost y genera una gráfica
de coste medio vs número de partículas para cada combinación c1–c2.
"""
def procesar_barrido_particulas(
    network,
    pso_type,
    particles_start,
    particles_end,
    particles_step,
    iterations_fixed,
    tm_index=1
):
    base_path = PROJECT_ROOT / "results" / network / pso_type

    resultados = defaultdict(dict)

    for config_dir in base_path.iterdir():
        if not config_dir.is_dir():
            continue

        # Ignorar sweep_figures u otros directorios
        if not config_dir.name.startswith("p"):
            continue

        particles, iterations, c1, c2, _, _ = parse_config_dir(config_dir.name)

        if iterations != iterations_fixed:
            continue

        if particles < particles_start or particles > particles_end:
            continue

        if (particles - particles_start) % particles_step != 0:
            continue

        results_path = config_dir / f"TM{tm_index}" / "results.json"
        if not results_path.exists():
            continue

        with open(results_path) as f:
            data = json.load(f)

        costs = [
            r["best_cost"]
            for r in data["results"]
            if r["best_cost"] is not None
        ]

        if costs:
            mean_cost = sum(costs) / len(costs)
            resultados[(c1, c2)][particles] = mean_cost

    # ---- Pintar ----
    plt.rcParams.update({
        "font.size": fuente,
        "axes.labelsize": fuente_eje,
        "legend.fontsize": fuente_leyenda
    })
    plt.figure(figsize=fs)

    for (c1, c2), valores in sorted(resultados.items()):
        xs = sorted(valores.keys())
        ys = [valores[x] for x in xs]
        plt.plot(xs, ys, marker="o", label=f"c1={c1}, c2={c2}")

    plt.title(f"{network} - {pso_type} - TM{tm_index}\nCoste medio vs Partículas (iter={iterations_fixed})")
    plt.xlabel("Número de partículas")
    plt.ylabel("Coste medio (gCO₂/kWh)")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()

    output_dir = (
            PROJECT_ROOT /
            "results" /
            network /
            pso_type /
            "sweep_figures"
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    filename = (
        f"particulas_{particles_start}-{particles_end}_"
        f"i{iterations_fixed}.pdf"
    )
    plt.savefig(
        output_dir / filename,
        format="pdf",
        dpi=600,
        bbox_inches="tight"
    )

    plt.show()

    return resultados


"""
Calcula la media de best_cost y genera una gráfica
de coste medio vs número de partículas para cada combinación c1–c2.
Añade un sombreado a cada gráfica que representa el valor mínimo y máximo que
ha alcanzado a lo largo del barrido
"""
def procesar_barrido_particulas_min_max(
    network,
    pso_type,
    particles_start,
    particles_end,
    particles_step,
    iterations_fixed,
    tm_index=1
):
    from pathlib import Path
    import json
    import matplotlib.pyplot as plt
    from collections import defaultdict

    base_path = PROJECT_ROOT / "results" / network / pso_type
    resultados = defaultdict(dict)

    for config_dir in base_path.iterdir():
        if not config_dir.is_dir():
            continue

        # Ignorar sweep_figures u otros directorios
        if not config_dir.name.startswith("p"):
            continue

        particles, iterations, c1, c2, _, _ = parse_config_dir(config_dir.name)

        if iterations != iterations_fixed:
            continue

        if particles < particles_start or particles > particles_end:
            continue

        if (particles - particles_start) % particles_step != 0:
            continue

        results_path = config_dir / f"TM{tm_index}" / "results.json"
        if not results_path.exists():
            continue

        with open(results_path) as f:
            data = json.load(f)

        costs = [
            r["best_cost"]
            for r in data["results"]
            if r["best_cost"] is not None
        ]

        if costs:
            mean_cost = sum(costs) / len(costs)
            resultados[(c1, c2)][particles] = {
                "mean": mean_cost,
                "min": min(costs),
                "max": max(costs)
            }

    # ---- Pintar ----
    plt.rcParams.update({
        "font.size": fuente,
        "axes.labelsize": fuente_eje,
        "legend.fontsize": fuente_leyenda
    })
    plt.figure(figsize=fs)

    for (c1, c2), valores in sorted(resultados.items()):
        xs = sorted(valores.keys())
        ys_mean = [valores[x]["mean"] for x in xs]
        ys_min = [valores[x]["min"] for x in xs]
        ys_max = [valores[x]["max"] for x in xs]

        plt.plot(xs, ys_mean, marker="o", label=f"c1={c1}, c2={c2}")
        plt.fill_between(xs, ys_min, ys_max, alpha=0.2)

    plt.title(f"{network} - {pso_type} - TM{tm_index}\nCoste medio ± rango vs Partículas (iter={iterations_fixed})")
    plt.xlabel("Número de partículas")
    plt.ylabel("Coste medio (gCO₂/kWh)")
    plt.legend(title="c1–c2")
    plt.grid(True)
    plt.tight_layout()

    output_dir = (
            PROJECT_ROOT /
            "results" /
            network /
            pso_type /
            "sweep_figures"
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    filename = (
        f"particulas_{particles_start}-{particles_end}_"
        f"i{iterations_fixed}_minmax.pdf"
    )
    plt.savefig(
        output_dir / filename,
        format="pdf",
        dpi=600,
        bbox_inches="tight"
    )

    plt.show()

    return resultados


def plot_tm_bars_with_confidence(
    network,
    config_dir,
    tm_indices,
    confidence=0.95,
    pso_type="PSO"
):
    """
    Dibuja un gráfico de barras (una por TM) con intervalo de confianza adaptativo.
    """

    means = []
    ci_errors = []
    labels = []

    for tm in tm_indices:
        results_path = (
                PROJECT_ROOT /
                "results" /
                network /
                pso_type /
                config_dir /
                f"TM{tm}" /
                "results.json"
        )

        if not results_path.exists():
            raise FileNotFoundError(f"No existe {results_path}")

        with open(results_path) as f:
            data = json.load(f)

        # Extraer best_cost válidos
        costs = [
            r["best_cost"]
            for r in data["results"]
            if r["best_cost"] is not None
        ]

        if len(costs) < 2:
            raise ValueError(f"TM{tm}: no hay suficientes valores válidos")

        mean, ci = confidence_interval(costs, confidence)

        means.append(mean)
        ci_errors.append(ci)
        labels.append(f"TM{tm}")

    # ---- Gráfica ----
    plt.figure(figsize=(8, 6))
    plt.bar(
        labels,
        means,
        yerr=ci_errors,
        capsize=6
    )

    plt.ylabel("Coste medio (gCO₂/kWh)")
    plt.title(
        f"Coste medio por TM con IC {int(confidence*100)}%\n"
        f"{network} – {pso_type} – {config_dir}"
    )
    plt.grid(axis="y", linestyle="--", alpha=0.6)
    plt.tight_layout()
    plt.show()
import os
import re
import json
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from pathlib import Path
from datetime import datetime
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

    #plt.title(f"{network} - {pso_type} - TM{tm_index}\nCoste medio vs Iteraciones (particulas={particles_fixed})")
    plt.xlabel("Iteraciones")
    plt.ylabel("Emisiones (gCO₂)")
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

    #plt.title(f"{network} - {pso_type} - TM{tm_index}\nCoste medio ± rango vs Iteraciones (particulas={particles_fixed})")
    plt.xlabel("Iteraciones")
    plt.ylabel("Emisiones (gCO₂)")
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

    #plt.title(f"{network} - {pso_type} - TM{tm_index}\nCoste medio vs Partículas (iter={iterations_fixed})")
    plt.xlabel("Número de partículas")
    plt.ylabel("Emisiones(gCO₂)")
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

    #plt.title(f"{network} - {pso_type} - TM{tm_index}\nCoste medio ± rango vs Partículas (iter={iterations_fixed})")
    plt.xlabel("Número de partículas")
    plt.ylabel("Emisiones (gCO₂)")
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
    plt.rcParams.update({
        "font.size": fuente,
        "axes.labelsize": fuente_eje,
        "legend.fontsize": fuente_leyenda
    })
    plt.figure(figsize=fs)

    plt.bar(
        labels,
        means,
        yerr=ci_errors,
        capsize=6,
        color='#27AE60'
    )

    plt.ylabel("Emisiones (gCO₂)")
    plt.grid(axis="y", linestyle="--", alpha=0.6)
    plt.tight_layout()

    output_dir = (
            PROJECT_ROOT /
            "results" /
            network /
            pso_type /
            config_dir /
            "figures"
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    filename = (
        f"{config_dir}_runs.pdf"
    )
    plt.savefig(
        output_dir / filename,
        format="pdf",
        dpi=600,
        bbox_inches="tight"
    )

    plt.show()

def plot_all_runs_iteraciones(
    network,
    pso_type,
    iter_start,
    iter_end,
    iter_step,
    particles_fixed,
    tm_index=1
):
    base_path = PROJECT_ROOT / "results" / network / pso_type

    resultados = defaultdict(list)

    for config_dir in base_path.iterdir():
        if not config_dir.is_dir():
            continue

        if not config_dir.name.startswith("p"):
            continue

        try:
            particles, iterations, c1, c2, _, k = parse_config_dir(config_dir.name)
        except:
            continue

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

        for run in data["results"]:
            cost = run["best_cost"]
            if cost is not None:
                resultados[iterations].append(cost)

    # ---- PINTAR ----
    plt.rcParams.update({
        "font.size": fuente,
        "axes.labelsize": fuente_eje,
        "legend.fontsize": fuente_leyenda
    })
    plt.figure(figsize=fs)

    # Scatter de todos los runs
    for iteration, costs in resultados.items():
        xs = [iteration] * len(costs)
        plt.scatter(xs, costs, alpha=0.5)

    # Media superpuesta
    xs_mean = sorted(resultados.keys())
    ys_mean = [sum(resultados[i]) / len(resultados[i]) for i in xs_mean]

    plt.plot(xs_mean, ys_mean, marker="o", linewidth=2)

    plt.xlabel("Iteraciones")
    plt.ylabel("Emisiones (gCO₂)")
    plt.grid(True)
    plt.tight_layout()

    output_dir = (
            PROJECT_ROOT /
            "results" /
            network /
            pso_type /
            "figures"
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    filename = (
        f"p{particles_fixed}_"
        f"iterations_{iter_start}-{iter_end}.pdf"
    )
    plt.savefig(
        output_dir / filename,
        format="pdf",
        dpi=600,
        bbox_inches="tight"
    )

    plt.show()

    return resultados








def procesar_barrido_iteraciones_regex(
    directory,
    regex_pattern,
    iter_start,
    iter_end,
    iter_step,
    particles_fixed,
    start_datetime=None,
    end_datetime=None
):
    resultados = defaultdict(dict)

    pattern = re.compile(regex_pattern, re.VERBOSE)

    for file in directory.iterdir():
        if not file.is_file():
            continue

        match = pattern.match(file.name)
        if not match:
            continue

        # --- Extraer parámetros ---
        particles = int(match.group("particles"))
        iterations = int(match.group("iters"))
        c1 = float(match.group("c1"))
        c2 = float(match.group("c2"))
        date = match.group("date")
        time = match.group("time")

        # --- Filtrar partículas ---
        if particles != particles_fixed:
            continue

        # --- Filtrar rango de iteraciones ---
        if iterations < iter_start or iterations > iter_end:
            continue

        if (iterations - iter_start) % iter_step != 0:
            continue

        # --- Filtrar por fecha/hora ---
        if start_datetime or end_datetime:
            dt = datetime.strptime(date + time, "%Y%m%d%H%M%S")

            if start_datetime and dt < start_datetime:
                continue
            if end_datetime and dt > end_datetime:
                continue

        # --- Leer JSON ---
        try:
            with open(file) as f:
                data = json.load(f)
        except Exception as e:
            print(f"Error en {file}: {e}")
            continue

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

    plt.xlabel("Iteraciones")
    plt.ylabel("Emisiones (gCO₂)")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()

    output_dir = (
            PROJECT_ROOT /
            "results/Abilene/sweeps/figures/sweeps_with_init"
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    filename = (
        f"p{particles_fixed}_"
        f"iterations_{iter_start}-{iter_end}.pdf"
    )
    plt.savefig(
        output_dir / filename,
        format="pdf",
        dpi=600,
        bbox_inches="tight"
    )

    plt.show()

    return resultados





def procesar_barrido_particulas_regex(
    directory,
    regex_pattern,
    particles_start,
    particles_end,
    particles_step,
    iterations_fixed=1500,
    start_datetime=None,
    end_datetime=None
):
    resultados = defaultdict(dict)

    pattern = re.compile(regex_pattern, re.VERBOSE)

    for file in directory.iterdir():
        if not file.is_file():
            continue

        match = pattern.match(file.name)
        if not match:
            continue

        # --- Extraer parámetros ---
        particles = int(match.group("particles"))
        iterations = int(match.group("iters"))
        c1 = float(match.group("c1"))
        c2 = float(match.group("c2"))
        date = match.group("date")
        time = match.group("time")

        # --- Filtrar tipo de experimento ---
        # (solo barrido de partículas)
        if iterations != iterations_fixed:
            continue

        # --- Filtrar rango de partículas ---
        if particles < particles_start or particles > particles_end:
            continue

        if (particles - particles_start) % particles_step != 0:
            continue

        # --- Filtrar por fecha/hora ---
        if start_datetime or end_datetime:
            dt = datetime.strptime(date + time, "%Y%m%d%H%M%S")

            if start_datetime and dt < start_datetime:
                continue
            if end_datetime and dt > end_datetime:
                continue

        # --- Leer JSON ---
        try:
            with open(file) as f:
                data = json.load(f)
        except Exception as e:
            print(f"Error en {file}: {e}")
            continue

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
        xs = sorted(valores.keys())  # partículas
        ys = [valores[x] for x in xs]
        plt.plot(xs, ys, marker="o", label=f"c1={c1}, c2={c2}")

    plt.xlabel("Partículas")
    plt.ylabel("Emisiones (gCO₂)")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()

    output_dir = (
            PROJECT_ROOT /
            "results/Abilene/sweeps/figures/sweeps_with_init"
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    filename = (
        f"p{iterations_fixed}_"
        f"iterations_{particles_start}-{particles_end}.pdf"
    )
    plt.savefig(
        output_dir / filename,
        format="pdf",
        dpi=600,
        bbox_inches="tight"
    )

    plt.show()

    return resultados


import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap


def plot_costes_por_tm_ordenado(resultados_por_tm):
    plt.rcParams.update({
        "font.size": fuente,
        "axes.labelsize": fuente_eje,
        "legend.fontsize": fuente_leyenda
    })

    tms = sorted(resultados_por_tm.keys())

    cmap = LinearSegmentedColormap.from_list(
        "verde_naranja",
        ["#27AE60", "#F1C40F", "#E67E22"]
    )

    plt.figure(figsize=fs)

    width = 0.12
    separacion_grupos = 1.2

    # Para construir la leyenda sin duplicados
    legend_handles = {}

    for i, tm in enumerate(tms):
        datos_tm = resultados_por_tm[tm]

        # Ordenar por coste
        items_ordenados = sorted(datos_tm.items(), key=lambda x: x[1])

        n = len(items_ordenados)
        x_base = i * separacion_grupos

        for j, (label, valor) in enumerate(items_ordenados):
            color = cmap(j / (n - 1)) if n > 1 else cmap(0)

            bar = plt.bar(
                x_base + j * width,
                valor,
                width,
                color=color
            )

            # Guardar handle para leyenda (solo una vez por label)
            if label not in legend_handles:
                legend_handles[label] = bar[0]

    # Centrar etiquetas de TM
    xticks = [
        i * separacion_grupos + width * 2
        for i in range(len(tms))
    ]

    plt.xticks(xticks, tms)

    plt.ylabel("Emisiones (gCO₂)")

    plt.legend(
        legend_handles.values(),
        legend_handles.keys(),
        loc="lower center",
        bbox_to_anchor=(0.5, 1.02),
        ncol=3,
        frameon=False
    )

    plt.grid(axis="y")
    plt.tight_layout()

    output_dir = (
            PROJECT_ROOT /
            "results/Geant"
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    filename = (
        f"Geant_comparative_emissions_all_conf.pdf"
    )
    plt.savefig(
        output_dir / filename,
        format="pdf",
        dpi=600,
        bbox_inches="tight"
    )

    plt.show()

import os
import re
import json
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from collections import defaultdict
from libs.utils import confidence_interval

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
Lee los archivos JSON de resultados generados el día 7 (20251107),
calcula el coste medio (ignorando valores nulos),
y pinta la gráfica de coste medio vs iteraciones.
"""
def procesar_resultados_particles_fijas_y_pintar(directorio="."):
    # Regex para extraer iteraciones, c1 y c2

    # pattern = re.compile(
    #     r"^200particles_(?P<iters>1[0-4]00|1500)iters_"
    #     r"(?P<c1>1\.5|1\.75|2\.0|2\.25|2\.5)c1_"
    #     r"(?P<c2>2\.5|2\.25|2\.0|1\.75|1\.5)c2_"
    #     r"0\.7w_100k_20251107_\d{6}\.json$"
    # )


    pattern = re.compile(
        r"^20260123_\d{6}_"
        r"200particles_(?P<iters>1[0-4]00|1500)iters_"
        r"(?P<c1>1\.5|1\.75|2\.0|2\.25|2\.5)c1_"
        r"(?P<c2>2\.5|2\.25|2\.0|1\.75|1\.5)c2_"
        r"0\.7w_100k\.json$"
    )

    # Estructura: {(c1, c2): {iters: media_coste}}
    resultados = defaultdict(dict)

    for f in os.listdir(directorio):
        match = pattern.match(f)
        if not match:
            continue

        iters = int(match.group("iters"))
        c1 = float(match.group("c1"))
        c2 = float(match.group("c2"))

        with open(os.path.join(directorio, f)) as file:
            data = json.load(file)

        # Extraer best_cost válidos
        best_costs = [
            run["best_cost"] for run in data.get("results", [])
            if run["best_cost"] is not None
        ]

        if best_costs:  # si hay al menos un valor válido
            media_coste = sum(best_costs) / len(best_costs)
            resultados[(c1, c2)][iters] = media_coste

    # --- Pintar ---
    plt.figure(figsize=(8, 6))
    for (c1, c2), valores in sorted(resultados.items()):
        xs = sorted(valores.keys())
        ys = [valores[x] for x in xs]
        plt.plot(xs, ys, marker="o", label=f"c1={c1}, c2={c2}")

    plt.title("Coste medio vs número de iteraciones (partículas fijas en 200)")
    plt.xlabel("Iteraciones")
    plt.ylabel("Coste medio (gCO2/kWh)")
    plt.legend(title="Parámetros")
    plt.grid(True)
    plt.tight_layout()
    plt.show()

    return resultados


"""
Procesa archivos generados con el script donde las iteraciones varían (1000–1500),
c1 aumenta y c2 disminuye. Calcula media, mínimo y máximo de best_cost
(ignorando nulos) y genera una gráfica con banda de variabilidad.
"""
def procesar_resultados_particles_fijas_min_max_y_pintar(directorio="."):
    # Regex: timestamp al final, fecha fija 20251107

    # pattern = re.compile(
    #     r"^200particles_(?P<iters>1[0-4]00|1500)iters_"
    #     r"(?P<c1>1\.5|1\.75|2\.0|2\.25|2\.5)c1_"
    #     r"(?P<c2>2\.5|2\.25|2\.0|1\.75|1\.5)c2_"
    #     r"0\.7w_100k_20251107_\d{6}\.json$"
    # )

    pattern = re.compile(
        r"^20260123_\d{6}_"
        r"200particles_(?P<iters>1[0-4]00|1500)iters_"
        r"(?P<c1>1\.5|1\.75|2\.0|2\.25|2\.5)c1_"
        r"(?P<c2>2\.5|2\.25|2\.0|1\.75|1\.5)c2_"
        r"0\.7w_100k\.json$"
    )

    # Estructura: {(c1, c2): {iters: {"mean": x, "min": y, "max": z}}}
    resultados = defaultdict(dict)

    for f in os.listdir(directorio):
        match = pattern.match(f)
        if not match:
            continue

        iters = int(match.group("iters"))
        c1 = float(match.group("c1"))
        c2 = float(match.group("c2"))

        with open(os.path.join(directorio, f)) as file:
            data = json.load(file)

        # Extraer best_cost válidos
        best_costs = [
            run["best_cost"] for run in data.get("results", [])
            if run["best_cost"] is not None
        ]

        if best_costs:
            mean_cost = sum(best_costs) / len(best_costs)
            min_cost = min(best_costs)
            max_cost = max(best_costs)
            resultados[(c1, c2)][iters] = {
                "mean": mean_cost,
                "min": min_cost,
                "max": max_cost
            }

    # --- Pintar ---
    plt.figure(figsize=(9, 6))

    for (c1, c2), valores in sorted(resultados.items()):
        xs = sorted(valores.keys())
        ys_mean = [valores[x]["mean"] for x in xs]
        ys_min = [valores[x]["min"] for x in xs]
        ys_max = [valores[x]["max"] for x in xs]

        # Dibujar línea de la media
        plt.plot(xs, ys_mean, marker="o", label=f"c1={c1}, c2={c2}")

        # Dibujar rango [min, max] como banda
        plt.fill_between(xs, ys_min, ys_max, alpha=0.2)

    plt.title("Coste medio (± rango) vs Iteraciones\nc1–c2 variables, 200 partículas")
    plt.xlabel("Iteraciones")
    plt.ylabel("Coste medio (ignorando nulos)")
    plt.legend(title="Parámetros c1–c2")
    plt.grid(True)
    plt.tight_layout()
    plt.show()

    return resultados


"""
Procesa archivos generados con el script de iteraciones fijas (1500),
donde c1 aumenta, c2 disminuye y particles varía de 100 a 500.
Calcula la media de best_cost (ignorando nulos) y genera una gráfica
de coste medio vs número de partículas para cada combinación c1–c2.
"""
def procesar_resultados_iter_fijas_y_pintar(directorio="."):
    # Regex: timestamp al inicio, fecha fija 20251107
    pattern = re.compile(
        r"^20260123_\d{6}_"                  # timestamp del día de hoy
        r"(?P<particles>[1-5]00)particles_"
        r"1500iters_"
        r"(?P<c1>1\.5|1\.75|2\.0|2\.25|2\.5)c1_"
        r"(?P<c2>2\.5|2\.25|2\.0|1\.75|1\.5)c2_"
        r"0\.7w_100k\.json$"
    )

    # Estructura: {(c1, c2): {particles: mean_cost}}
    resultados = defaultdict(dict)

    for f in os.listdir(directorio):
        match = pattern.match(f)
        if not match:
            continue

        particles = int(match.group("particles"))
        c1 = float(match.group("c1"))
        c2 = float(match.group("c2"))

        with open(os.path.join(directorio, f)) as file:
            data = json.load(file)

        # Extraer los best_cost válidos
        best_costs = [
            run["best_cost"] for run in data.get("results", [])
            if run["best_cost"] is not None
        ]

        if best_costs:
            mean_cost = sum(best_costs) / len(best_costs)
            resultados[(c1, c2)][particles] = mean_cost

    # --- Pintar ---
    plt.figure(figsize=(8, 6))
    for (c1, c2), valores in sorted(resultados.items()):
        xs = sorted(valores.keys())
        ys = [valores[x] for x in xs]
        plt.plot(xs, ys, marker="o", label=f"c1={c1}, c2={c2}")

    plt.title("Coste medio vs número de partículas (iteraciones fijas en 1500)")
    plt.xlabel("Número de partículas")
    plt.ylabel("Coste medio (gCO2/kWh)")
    plt.legend(title="Parámetros c1–c2")
    plt.grid(True)
    plt.tight_layout()
    plt.show()

    return resultados


"""
Procesa archivos generados con el script de iteraciones fijas (1500),
donde c1 aumenta, c2 disminuye y particles varía de 100 a 500.
Calcula media, mínimo y máximo de best_cost (ignorando nulos),
y pinta una gráfica de coste medio vs número de partículas.
"""
def procesar_resultados_iter_fijas_min_max_y_pintar(directorio="."):
    # Regex: timestamp al inicio, fecha fija 20251107
    pattern = re.compile(
        r"^20260123_\d{6}_"                  # timestamp del día actual
        r"(?P<particles>[1-5]00)particles_"
        r"1500iters_"
        r"(?P<c1>1\.5|1\.75|2\.0|2\.25|2\.5)c1_"
        r"(?P<c2>2\.5|2\.25|2\.0|1\.75|1\.5)c2_"
        r"0\.7w_100k\.json$"
    )

    # Estructura: {(c1, c2): {particles: {"mean": x, "min": y, "max": z}}}
    resultados = defaultdict(dict)

    for f in os.listdir(directorio):
        match = pattern.match(f)
        if not match:
            continue

        particles = int(match.group("particles"))
        c1 = float(match.group("c1"))
        c2 = float(match.group("c2"))

        with open(os.path.join(directorio, f)) as file:
            data = json.load(file)

        # Extraer best_cost válidos
        best_costs = [
            run["best_cost"] for run in data.get("results", [])
            if run["best_cost"] is not None
        ]

        if best_costs:
            mean_cost = sum(best_costs) / len(best_costs)
            min_cost = min(best_costs)
            max_cost = max(best_costs)
            resultados[(c1, c2)][particles] = {
                "mean": mean_cost,
                "min": min_cost,
                "max": max_cost
            }

    # --- Pintar ---
    plt.figure(figsize=(9, 6))

    for (c1, c2), valores in sorted(resultados.items()):
        xs = sorted(valores.keys())
        ys_mean = [valores[x]["mean"] for x in xs]
        ys_min = [valores[x]["min"] for x in xs]
        ys_max = [valores[x]["max"] for x in xs]

        # Dibujar línea media
        plt.plot(xs, ys_mean, marker="o", label=f"c1={c1}, c2={c2}")

        # Sombrear rango [min, max]
        plt.fill_between(xs, ys_min, ys_max, alpha=0.2)

    plt.title("Coste medio (± rango) vs número de partículas\n(Iteraciones fijas en 1500)")
    plt.xlabel("Número de partículas")
    plt.ylabel("Coste medio (ignorando nulos)")
    plt.legend(title="Parámetros c1–c2")
    plt.grid(True)
    plt.tight_layout()
    plt.show()

    return resultados


def plot_tm_bars_with_confidence(
    network,
    config_dir,
    tm_indices,
    confidence=0.95
):
    """
    Dibuja un gráfico de barras (una por TM) con intervalo de confianza adaptativo.
    """

    means = []
    ci_errors = []
    labels = []

    for tm in tm_indices:
        results_path = Path(
            f"results/{network}/PSO/{config_dir}/TM{tm}/results.json"
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

    plt.ylabel("Coste medio (gCO2/kWh)")
    plt.title(
        f"Coste medio por TM con IC {int(confidence*100)}%\n"
        f"{network} – {config_dir}"
    )
    plt.grid(axis="y", linestyle="--", alpha=0.6)
    plt.tight_layout()
    plt.show()
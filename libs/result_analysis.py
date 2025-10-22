import json
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt

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

        # tomar coste promedio por iteración (por si hay varias runs)
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

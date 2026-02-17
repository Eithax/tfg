import math
from scipy.stats import t, norm

def confidence_interval(values, confidence=0.95):
    n = len(values)
    mean = sum(values) / n
    std = math.sqrt(sum((x - mean) ** 2 for x in values) / (n - 1))

    alpha = 1 - confidence

    if n < 30:
        factor = t.ppf(1 - alpha / 2, df=n - 1)
    else:
        factor = norm.ppf(1 - alpha / 2)

    ci = factor * std / math.sqrt(n)
    return mean, ci

def parse_config_dir(config_dir):
    parts = config_dir.split("_")

    particles = int(parts[0][1:])
    iterations = int(parts[1][1:])
    c1 = float(parts[2].split("-")[1])
    c2 = float(parts[3].split("-")[1])
    w = float(parts[4][1:])
    k = int(parts[5][1:])

    return particles, iterations, c1, c2, w, k

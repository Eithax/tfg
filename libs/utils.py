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

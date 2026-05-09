import numpy as np
import matplotlib.pyplot as plt

fig, ax = plt.subplots(figsize=(10, 10), facecolor='white')
ax.set_facecolor('white')
ax.set_aspect('equal')
ax.axis('off')

lim = 8.0

# --- Tareas y sus ángulos (distribuidas uniformemente, empezando arriba) ---
tareas = [
    "Definición y\nrefinamiento\ndel problema",
    "Análisis y\nestudio",
    "Diseño de\nla solución",
    "Implementación",
    "Pruebas",
    "Reunión con\nlos tutores",
    "Actualización\nde la memoria",
]

n = len(tareas)
# Ángulos de cada sector (en radianes), empezando desde arriba (pi/2) en sentido antihorario
angulos = [np.pi / 2 - i * 2 * np.pi / n for i in range(n)]

# --- Líneas de sector ---
for ang in angulos:
    ax.plot([0, lim * 0.9 * np.cos(ang)], [0, lim * 0.9 * np.sin(ang)],
            color='black', linewidth=0.9, zorder=2)

# --- Espiral naranja ---
n_ciclos = 3
r_inicio = 0.15
r_fin = 5.8

thetas = np.linspace(0, n_ciclos * 2 * np.pi, 2000)
rs = np.linspace(r_inicio, r_fin, len(thetas))

# Empieza en la parte superior (pi/2) y gira en sentido horario (- thetas)
xs = rs * np.cos(np.pi / 2 - thetas)
ys = rs * np.sin(np.pi / 2 - thetas)

ax.plot(xs, ys, color='#E8450A', linewidth=7.5, solid_capstyle='round',
        solid_joinstyle='round', zorder=3)

# Punto central
ax.plot(0, 0, 'o', color='#E8450A', markersize=8, zorder=4)

# --- Etiquetas de las tareas ---
r_label = lim * 0.78
for i, tarea in enumerate(tareas):
    ang = angulos[i] - np.pi / n
    x = r_label * np.cos(ang)
    y = r_label * np.sin(ang)

    # Alineación según posición
    if x > 0.5:
        ha = 'left'
    elif x < -0.5:
        ha = 'right'
    else:
        ha = 'center'

    if y > 0.5:
        va = 'bottom'
    elif y < -0.5:
        va = 'top'
    else:
        va = 'center'

    ax.text(x, y, tarea, ha=ha, va=va, fontsize=16, color='black')

ax.set_xlim(-lim, lim)
ax.set_ylim(-lim, lim)

plt.tight_layout()
#plt.savefig('/mnt/user-data/outputs/espiral_v3.png', dpi=150,
#            bbox_inches='tight', facecolor='white')
output = "espiral.pdf"
plt.savefig(
    output,
    format="pdf",
    dpi=600,
    bbox_inches="tight"
)
plt.show()
print("Guardado.")
import matplotlib.pyplot as plt

# Iteraciones (x) y coste (y)
iteraciones = [100, 200, 300, 400, 500]

costes_matriz1_iter = [63.788785, 61.294874, 59.322238, 57.434496, 56.407230]
costes_matriz2_iter = [68.325458, 64.522757, 61.397983, 59.014523, 58.116651]
costes_matriz3_iter = [75.537161, 70.402544, 69.64638, 68.554955, 65.734510]
costes_matriz4_iter = [85.151745, 81.065431, 78.334537, 76.117233, 75.46331]
# costes_matriz5_iter = []

# Tiempo (x) y coste (y)
tiemposTM1 = [4, 9, 14, 19, 24]
tiemposTM2 = [4, 9, 14, 19, 24]
tiemposTM3 = [4, 9, 14, 18, 22]
tiemposTM4 = [4, 9, 13, 18, 22]
# tiemposTM5 = []

costes_matriz1_time = [63.788785, 61.294874, 59.322238, 57.434496, 56.407230]
costes_matriz2_time = [68.325458, 64.522757, 61.397983, 59.014523, 58.116651]
costes_matriz3_time = [75.537161, 70.402544, 69.64638, 68.554955, 65.734510]
costes_matriz4_time = [85.151745, 81.065431, 78.334537, 76.117233, 75.46331]
# costes_matriz5_time = []

# ====== GRÁFICA 1: Iteraciones vs Coste ======
plt.figure(figsize=(7,5))
plt.plot(iteraciones, costes_matriz1_iter, marker="o", label="TM1")
plt.plot(iteraciones, costes_matriz2_iter, marker="o", label="TM2")
plt.plot(iteraciones, costes_matriz3_iter, marker="o", label="TM3")
plt.plot(iteraciones, costes_matriz4_iter, marker="o", label="TM4")
# plt.plot(iteraciones, costes_matriz5_iter, marker="o", label="TM5")

plt.title("Iteraciones vs Coste")
plt.xlabel("Iteraciones")
plt.ylabel("Coste (gCO2/kWh)")
plt.legend()
plt.grid(True)
plt.show()

# ====== GRÁFICA 2: Tiempo vs Coste ======
plt.figure(figsize=(7,5))
plt.plot(tiemposTM1, costes_matriz1_time, marker="o", label="TM1")
plt.plot(tiemposTM2, costes_matriz2_time, marker="o", label="TM2")
plt.plot(tiemposTM3, costes_matriz3_time, marker="o", label="TM3")
plt.plot(tiemposTM4, costes_matriz4_time, marker="o", label="TM4")
#plt.plot(tiemposTM5, costes_matriz5_time, marker="o", label="TM5")

plt.title("Tiempo vs Coste")
plt.xlabel("Tiempo (s)")
plt.ylabel("Coste (gCO2/kWh)")
plt.legend()
plt.grid(True)
plt.show()

import re
import numpy as np
import tkinter as tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import random

# ============================
# EXTRAIR GRUPOS
# ============================

def extrair_grupos(texto):
    padrao = r'([a-zA-Z])(\d+)\s*\(\s*(-?\d+\.?\d*)\s*,\s*(-?\d+\.?\d*)\s*\)'
    encontrados = re.findall(padrao, texto)

    if not encontrados:
        raise ValueError("Nenhum ponto válido encontrado.")

    grupos_temp = {}

    for letra, numero, x, y in encontrados:
        numero = int(numero)

        if letra not in grupos_temp:
            grupos_temp[letra] = {}

        if numero in grupos_temp[letra]:
            raise ValueError(f"Ponto duplicado: {letra}{numero}")

        grupos_temp[letra][numero] = (float(x), float(y))

    grupos = {}

    for letra, pontos in grupos_temp.items():
        numeros = sorted(pontos.keys())

        if numeros != list(range(min(numeros), max(numeros)+1)):
            raise ValueError(f"Sequência incorreta no grupo '{letra}'")

        arr = np.array([pontos[n] for n in numeros])

        grupos[letra] = {
            "original": arr.copy(),
            "atual": arr.copy()
        }

    return grupos

# ============================
# CORES FIXAS POR GRUPO
# ============================

cores = {}

def cor_grupo(letra):
    if letra not in cores:
        cores[letra] = (random.random(), random.random(), random.random())
    return cores[letra]

# ============================
# DESENHAR
# ============================

def desenhar():
    ax.clear()
    ax.axhline(0)
    ax.axvline(0)
    ax.grid(True)

    for letra, dados in grupos.items():
        if not visibilidade[letra].get():
            continue

        pontos = dados["atual"]
        cor = cor_grupo(letra)

        x = np.append(pontos[:,0], pontos[0,0])
        y = np.append(pontos[:,1], pontos[0,1])

        ax.plot(x, y, color=cor, label=f"Grupo {letra}")
        ax.scatter(pontos[:,0], pontos[:,1], color=cor)

    ax.set_xlim(-20, 20)
    ax.set_ylim(-20, 20)
    ax.set_aspect('equal')
    ax.legend()
    canvas.draw()

# ============================
# ATUALIZAR A PARTIR DO TEXTO
# ============================

def atualizar_texto(event=None):
    global grupos, visibilidade

    texto = entrada.get("1.0", tk.END)

    try:
        novos_grupos = extrair_grupos(texto)
        grupos = novos_grupos

        # recriar checkboxes
        for widget in frame_checks.winfo_children():
            widget.destroy()

        visibilidade = {}

        for letra in grupos.keys():
            var = tk.BooleanVar(value=True)
            chk = tk.Checkbutton(frame_checks, text=f"Grupo {letra}", variable=var, command=desenhar)
            chk.pack(anchor="w")
            visibilidade[letra] = var

        status_label.config(text="✔ OK", fg="green")
        desenhar()

    except Exception as e:
        status_label.config(text=f"Erro: {e}", fg="red")

# ============================
# INTERFACE
# ============================

root = tk.Tk()
root.title("Plano Cartesiano Multi-Grupos")

frame_esq = tk.Frame(root)
frame_esq.pack(side=tk.LEFT, padx=10)

entrada = tk.Text(frame_esq, width=40, height=8)
entrada.pack()

entrada.insert(tk.END,
"""p1(1,1), p2(5,1), p3(5,4), p4(1,4)
b1(2,2), b2(6,2), b3(6,5), b4(2,5)"""
)

entrada.bind("<KeyRelease>", atualizar_texto)

frame_checks = tk.Frame(frame_esq)
frame_checks.pack(pady=5)

status_label = tk.Label(frame_esq, text="")
status_label.pack()

fig, ax = plt.subplots(figsize=(5,5))
canvas = FigureCanvasTkAgg(fig, master=root)
canvas.get_tk_widget().pack(side=tk.RIGHT)

grupos = {}
visibilidade = {}

atualizar_texto()

root.mainloop()
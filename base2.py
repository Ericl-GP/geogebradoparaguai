import re
import numpy as np
import tkinter as tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import random


# ============================================================
# 1. PROCESSAMENTO DE DADOS (PARSER)
# ============================================================

def extrair_grupos(texto):
    """
    Transforma texto bruto em matrizes numéricas (NumPy).
    Utiliza Expressões Regulares (Regex) para identificar padrões como 'a1(x, y)'.
    """
    # Regex: identifica uma letra, um número e as coordenadas dentro dos parênteses
    padrao = r'([a-zA-Z])(\d+)\s*\(\s*(-?\d+\.?\d*)\s*,\s*(-?\d+\.?\d*)\s*\)'
    encontrados = re.findall(padrao, texto)

    if not encontrados:
        raise ValueError("Nenhum ponto válido encontrado.")

    grupos_temp = {}
    for letra, numero, x, y in encontrados:
        if letra not in grupos_temp:
            grupos_temp[letra] = {}
        # Armazena cada ponto em um dicionário temporário para ordenar depois
        grupos_temp[letra][int(numero)] = (float(x), float(y))

    grupos_result = {}
    for letra, pontos in grupos_temp.items():
        # Ordena pelos índices (1, 2, 3...) para garantir que a linha siga a ordem correta
        numeros = sorted(pontos.keys())
        # Converte a lista de tuplas em uma Matriz NumPy [N linhas x 2 colunas]
        arr = np.array([pontos[n] for n in numeros])

        # Mantemos uma cópia 'original' para permitir o Reset das transformações
        grupos_result[letra] = {"original": arr.copy(), "atual": arr.copy()}

    return grupos_result


# ============================================================
# 2. MOTOR DE CÁLCULO (TRANSFORMAÇÕES GEOMÉTRICAS)
# ============================================================

def aplicar_transformacao(comando_externo=None):
    """
    Aplica álgebra linear sobre as matrizes de pontos.
    O 'exec' permite que fórmulas matemáticas digitadas pelo usuário
    sejam interpretadas como código Python em tempo de execução.
    """
    comando = comando_externo if comando_externo else entrada_math.get().strip()
    if not comando: return

    try:
        for letra, dados in grupos.items():
            if not visibilidade[letra].get(): continue

            # x e y aqui são vetores (colunas da matriz).
            # Operar sobre eles afeta todos os pontos simultaneamente (Vetorização)
            x = dados["atual"][:, 0]
            y = dados["atual"][:, 1]

            # Contexto matemático exposto para o usuário
            contexto = {
                'x': x, 'y': y, 'np': np,
                'sin': np.sin, 'cos': np.cos, 'tan': np.tan, 'pi': np.pi,
                'where': np.where  # Permite lógica: 'aumentar apenas se x > 0'
            }

            # Execução da fórmula (Ex: 'x = x + 2' move a figura inteira no eixo X)
            exec(comando, {}, contexto)

            # Devolve os vetores modificados para a matriz 'atual' do grupo
            dados["atual"][:, 0] = contexto['x']
            dados["atual"][:, 1] = contexto['y']

        status_label.config(text="✔ Transformação Aplicada", fg="blue")
        desenhar()
    except Exception as e:
        status_label.config(text=f"Erro: {e}", fg="red")


def resetar_pontos():
    """Restaura a matriz 'atual' para o estado da matriz 'original'."""
    for letra in grupos:
        grupos[letra]["atual"] = grupos[letra]["original"].copy()
    desenhar()
    status_label.config(text="🔄 Pontos Resetados", fg="orange")


# ============================================================
# 3. RENDERIZAÇÃO VISUAL (MATPLOTLIB)
# ============================================================

cores = {}


def cor_grupo(letra):
    """Garante que cada grupo (A, B, C...) tenha uma cor única e persistente."""
    if letra not in cores:
        cores[letra] = (random.random(), random.random(), random.random())
    return cores[letra]


def desenhar():
    """Limpa o plano cartesiano e redesenha as matrizes atualizadas."""
    ax.clear()
    ax.axhline(0, color='black', lw=1)  # Eixo X
    ax.axvline(0, color='black', lw=1)  # Eixo Y
    ax.grid(True, linestyle='--', alpha=0.6)

    for letra, dados in grupos.items():
        if not visibilidade[letra].get(): continue

        pontos = dados["atual"]
        cor = cor_grupo(letra)

        # Para fechar o polígono: anexa o primeiro ponto ao final da sequência
        xf = np.append(pontos[:, 0], pontos[0, 0])
        yf = np.append(pontos[:, 1], pontos[0, 1])

        # Desenha as linhas e os vértices (scatter)
        ax.plot(xf, yf, color=cor, label=f"Grupo {letra}", marker='o', markersize=4)

    ax.set_xlim(-20, 20)  # Limite fixo para visualizar a movimentação
    ax.set_ylim(-20, 20)
    ax.set_aspect('equal')  # Mantém a proporção (quadrado parece quadrado)
    ax.legend()
    canvas.draw()


# ============================================================
# 4. INTERFACE GRÁFICA (TKINTER)
# ============================================================

def atualizar_base(event=None):
    """Lê a caixa de texto de pontos e reconstrói os controles de visibilidade."""
    global grupos, visibilidade
    try:
        grupos = extrair_grupos(entrada_pontos.get("1.0", tk.END))
        for widget in frame_checks.winfo_children(): widget.destroy()
        visibilidade = {}
        for letra in grupos.keys():
            var = tk.BooleanVar(value=True)
            tk.Checkbutton(frame_checks, text=f"Grupo {letra}", variable=var,
                           command=desenhar).pack(anchor="w")
            visibilidade[letra] = var
        status_label.config(text="✔ Base carregada", fg="green")
        desenhar()
    except Exception as e:
        status_label.config(text=f"Erro: {e}", fg="red")


root = tk.Tk()
root.title("Geometria Analítica Computacional")

# Painel Lateral de Controle
frame_esq = tk.Frame(root, padx=10, pady=10)
frame_esq.pack(side=tk.LEFT, fill=tk.Y)

# Seção 1: Entrada de Pontos
tk.Label(frame_esq, text="1. Coordenadas dos Grupos:", font=("Arial", 9, "bold")).pack(anchor="w")
entrada_pontos = tk.Text(frame_esq, width=40, height=6, font=("Consolas", 10))
entrada_pontos.pack(pady=5)
entrada_pontos.insert(tk.END, "a1(1,1), a2(5,1), a3(5,5), a4(1,5)")
entrada_pontos.bind("<KeyRelease>", atualizar_base)

# Seção 2: Fórmulas Matemáticas
tk.Label(frame_esq, text="2. Cálculo de Transformação:", font=("Arial", 9, "bold")).pack(anchor="w")
entrada_math = tk.Entry(frame_esq, width=40, font=("Consolas", 10), fg="blue")
entrada_math.pack(pady=5)
entrada_math.insert(0, "x = x * 1.2; y = y * 1.2")  # Escala padrão

# Seção 3: Botões e Atalhos
frame_btns = tk.Frame(frame_esq)
frame_btns.pack(fill=tk.X, pady=5)

tk.Button(frame_btns, text="Executar Cálculo", command=aplicar_transformacao,
          bg="#e1f5fe", font=("Arial", 9, "bold")).pack(side=tk.LEFT, expand=True, fill=tk.X)

tk.Label(frame_esq, text="3. Transformações Prontas:", font=("Arial", 9, "bold")).pack(anchor="w", pady=(10, 0))
frame_atalhos = tk.Frame(frame_esq)
frame_atalhos.pack(fill=tk.X)

# Dicionário de funções geométricas aplicadas às matrizes
atalhos = [
    ("Girar 45°", "nx=x*cos(pi/4)-y*sin(pi/4); y=x*sin(pi/4)+y*cos(pi/4); x=nx"),
    ("Refletir Y", "x = -x"),
    ("Cisilhamento", "x = x + 0.5 * y"),
    ("Deformar x>0", "x = where(x > 0, x * 2, x)"),
    ("Reset", "RESET")
]

for nome, cmd in atalhos:
    if cmd == "RESET":
        btn = tk.Button(frame_atalhos, text=nome, command=resetar_pontos, fg="red")
    else:
        btn = tk.Button(frame_atalhos, text=nome, command=lambda c=cmd: aplicar_transformacao(c))
    btn.pack(side=tk.LEFT, padx=1, pady=2)

frame_checks = tk.Frame(frame_esq)
frame_checks.pack(pady=10, fill=tk.X)

status_label = tk.Label(frame_esq, text="Aguardando...", fg="gray")
status_label.pack(side=tk.BOTTOM)

# Painel Direito: O Gráfico
fig, ax = plt.subplots(figsize=(6, 6))
canvas = FigureCanvasTkAgg(fig, master=root)
canvas.get_tk_widget().pack(side=tk.RIGHT, expand=True, fill=tk.BOTH)

# Inicialização
atualizar_base()
root.mainloop()
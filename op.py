import matplotlib.pyplot as plt
import seaborn as sns

# --- Datos ---
data = {
    "Porcentaje de grandes empresas que aumentarán su presupuesto de IA": (74, "Estudio de IDC 1"),
    "Tasa de crecimiento del mercado chileno de IA": (26, "Estudio de IDC 1"),
    "Porcentaje de empresas que ya han adoptado la IA": (30, "ESE Business School 13"),
    "Porcentaje de empresas que planean aumentar la inversión en IA para 2025": (80, "Estudio de SAP 2"),
    "Retorno promedio de la inversión para iniciativas de IA": (3, "Estudio de IDC 1"), # Asumiendo 3x se refiere a 300% o un factor de 3
    "Porcentaje de organizaciones que implementan IA en menos de 6 meses": (49, "Estudio de IDC 1"),
    "Tiempo promedio para recuperar la inversión en IA": (16.8, "Estudio de IDC 1"),
    "Porcentaje de organizaciones que recuperan la inversión en IA en menos de 6 meses": (20, "Estudio de IDC 1"),
    "Porcentaje de empresas que recuperan la inversión en IA en menos de 12 meses": (63, "Estudio de IDC 1"),
}

# --- Estilo Elegante (puedes personalizar estos) ---
color_palette = sns.color_palette("viridis", 9) # Paleta de colores elegante
sns.set_theme(style="whitegrid") # Estilo general del gráfico

font_title = {'family': 'serif', 'color':  '#333333', 'weight': 'bold', 'size': 14}
font_label = {'family': 'serif', 'color':  '#555555', 'weight': 'normal', 'size': 12}


# --- Funciones para crear diferentes tipos de gráficos ---

def crear_grafico_donut(titulo, porcentaje, fuente, color=color_palette[0], filename="donut_chart.png"):
    """Crea un gráfico de donut para un porcentaje."""
    fig, ax = plt.subplots(figsize=(8, 8))
    ax.pie([porcentaje, 100 - porcentaje],
           labels=[f'{porcentaje}%', ''],
           colors=[color, '#EEEEEE'],
           startangle=90,
           wedgeprops=dict(width=0.4), # Ancho del "donut"
           textprops={'fontsize': 16, 'color': '#333333', 'weight': 'bold'}) # Estilo del texto del porcentaje

    centre_circle = plt.Circle((0, 0), 0.6, fc='white') # Círculo blanco en el centro
    fig.gca().add_artist(centre_circle)

    ax.set_title(titulo, fontdict=font_title, pad=20)
    plt.text(0, -0.15, fuente, ha='center', va='center', fontsize=10, color='#777777') # Fuente abajo del título

    plt.tight_layout()
    plt.savefig(filename, dpi=300, bbox_inches='tight') # Guarda con alta resolución
    plt.show()


def crear_grafico_barras_horizontal(titulo, valor, unidad, fuente, color=color_palette[1], filename="bar_horizontal_chart.png"):
    """Crea un gráfico de barras horizontal para un valor."""
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.barh(y=1, width=valor, color=color, height=0.6) # Barra horizontal

    ax.set_yticks([]) # Sin ticks en el eje Y
    ax.set_xticks([]) # Sin ticks en el eje X
    ax.set_frame_on(False) # Sin marco alrededor del gráfico

    ax.text(0, 1, titulo, va='center', ha='left', fontdict=font_title) # Título a la izquierda
    ax.text(valor + 1, 1, f'{valor}{unidad}', va='center', ha='left', fontsize=16, color='#333333', weight='bold') # Valor a la derecha de la barra
    plt.text(0, 0.5, fuente, ha='left', va='center', fontsize=10, color='#777777') # Fuente abajo

    plt.xlim(0, valor * 1.2) # Ajusta el límite X para que quepa el valor
    plt.tight_layout()
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    plt.show()


def crear_grafico_barras_vertical(titulo, valor, unidad, fuente, color=color_palette[2], filename="bar_vertical_chart.png"):
    """Crea un gráfico de barras vertical para un valor."""
    fig, ax = plt.subplots(figsize=(6, 8))
    ax.bar(x=1, height=valor, color=color, width=0.6) # Barra vertical

    ax.set_xticks([]) # Sin ticks en el eje X
    ax.set_yticks([]) # Sin ticks en el eje Y
    ax.set_frame_on(False) # Sin marco

    ax.text(1, 0, titulo, ha='center', va='bottom', fontdict=font_title) # Título abajo
    ax.text(1, valor + 1, f'{valor}{unidad}', ha='center', va='bottom', fontsize=16, color='#333333', weight='bold') # Valor arriba de la barra
    plt.text(1, -2, fuente, ha='center', va='top', fontsize=10, color='#777777') # Fuente abajo del título

    plt.ylim(0, valor * 1.2) # Ajusta el límite Y
    plt.tight_layout()
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    plt.show()


def crear_grafico_barras_apiladas(titulo, porcentaje_principal, porcentaje_total, fuente, color_principal=color_palette[3], color_resto='#EEEEEE', filename="bar_apilada_chart.png"):
    """Crea un gráfico de barras apiladas para mostrar una parte de un total."""
    fig, ax = plt.subplots(figsize=(8, 4))

    # Barra principal (porcentaje clave)
    ax.barh(y=1, width=porcentaje_principal, color=color_principal, height=0.6, label='Porcentaje Clave')
    # Barra restante (para completar hasta 100%)
    ax.barh(y=1, width=porcentaje_total - porcentaje_principal, left=porcentaje_principal, color=color_resto, height=0.6, label='Resto')

    ax.set_yticks([]) # Sin ticks en el eje Y
    ax.set_xticks([]) # Sin ticks en el eje X
    ax.set_frame_on(False) # Sin marco

    ax.text(0, 1, titulo, va='center', ha='left', fontdict=font_title) # Título a la izquierda
    ax.text(porcentaje_principal + 1, 1, f'{porcentaje_principal}%', va='center', ha='left', fontsize=16, color='#333333', weight='bold') # Valor principal
    plt.text(0, 0.5, fuente, ha='left', va='center', fontsize=10, color='#777777') # Fuente abajo

    plt.xlim(0, porcentaje_total * 1.1) # Ajusta el límite X
    plt.tight_layout()
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    plt.show()


# --- Generar los gráficos para cada dato ---

# 1. Donut para porcentaje de empresas que aumentarán presupuesto
crear_grafico_donut(
    titulo="Grandes Empresas Aumentarán Presupuesto IA",
    porcentaje=data["Porcentaje de grandes empresas que aumentarán su presupuesto de IA"][0],
    fuente=f"Fuente: {data['Porcentaje de grandes empresas que aumentarán su presupuesto de IA'][1]}",
    filename="donut_presupuesto_empresas.png"
)

# 2. Barras horizontales para tasa de crecimiento
crear_grafico_barras_horizontal(
    titulo="Crecimiento Mercado IA en Chile",
    valor=data["Tasa de crecimiento del mercado chileno de IA"][0],
    unidad="%",
    fuente=f"Fuente: {data['Tasa de crecimiento del mercado chileno de IA'][1]}",
    filename="bar_crecimiento_mercado.png"
)

# 3. Donut para porcentaje de empresas que ya adoptaron IA
crear_grafico_donut(
    titulo="Empresas Chilenas Ya Adoptaron IA",
    porcentaje=data["Porcentaje de empresas que ya han adoptado la IA"][0],
    fuente=f"Fuente: {data['Porcentaje de empresas que ya han adoptado la IA'][1]}",
    color=color_palette[2], # Otro color para variar
    filename="donut_adopcion_empresas.png"
)

# 4. Donut para porcentaje de empresas que planean aumentar inversión
crear_grafico_donut(
    titulo="Empresas Planeando Aumentar Inversión en IA (2025)",
    porcentaje=data["Porcentaje de empresas que planean aumentar la inversión en IA para 2025"][0],
    fuente=f"Fuente: {data['Porcentaje de empresas que planean aumentar la inversión en IA para 2025'][1]}",
    color=color_palette[3],
    filename="donut_inversion_futura.png"
)

# 5. Barras verticales para retorno de inversión (factor)
crear_grafico_barras_vertical(
    titulo="Retorno Promedio de Inversión en IA",
    valor=data["Retorno promedio de la inversión para iniciativas de IA"][0],
    unidad="x Costo",
    fuente=f"Fuente: {data['Retorno promedio de la inversión para iniciativas de IA'][1]}",
    color=color_palette[4],
    filename="bar_retorno_inversion.png"
)

# 6. Donut para implementación rápida de IA
crear_grafico_donut(
    titulo="Organizaciones Implementan IA en Menos de 6 Meses",
    porcentaje=data["Porcentaje de organizaciones que implementan IA en menos de 6 meses"][0],
    fuente=f"Fuente: {data['Porcentaje de organizaciones que implementan IA en menos de 6 meses'][1]}",
    color=color_palette[5],
    filename="donut_implementacion_rapida.png"
)

# 7. Barras horizontales para tiempo promedio de recuperación
crear_grafico_barras_horizontal(
    titulo="Tiempo Promedio para Recuperar Inversión en IA",
    valor=data["Tiempo promedio para recuperar la inversión en IA"][0],
    unidad=" meses",
    fuente=f"Fuente: {data['Tiempo promedio para recuperar la inversión en IA'][1]}",
    color=color_palette[6],
    filename="bar_tiempo_recuperacion.png"
)

# 8. Barras apiladas para recuperación rápida de inversión (< 6 meses)
crear_grafico_barras_apiladas(
    titulo="Organizaciones Recuperan Inversión en < 6 Meses",
    porcentaje_principal=data["Porcentaje de organizaciones que recuperan la inversión en IA en menos de 6 meses"][0],
    porcentaje_total=100, # El total es 100%
    fuente=f"Fuente: {data['Porcentaje de organizaciones que recuperan la inversión en IA en menos de 6 meses'][1]}",
    color_principal=color_palette[7],
    filename="bar_apilada_recuperacion_rapida.png"
)

# 9. Barras apiladas para recuperación en menos de 12 meses
crear_grafico_barras_apiladas(
    titulo="Empresas Recuperan Inversión en < 12 Meses",
    porcentaje_principal=data["Porcentaje de empresas que recuperan la inversión en IA en menos de 12 meses"][0],
    porcentaje_total=100,
    fuente=f"Fuente: {data['Porcentaje de empresas que recuperan la inversión en IA en menos de 12 meses'][1]}",
    color_principal=color_palette[8],
    filename="bar_apilada_recuperacion_12meses.png"
)


print("Gráficos generados y guardados como archivos PNG.")
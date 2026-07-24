"""
EDA — Análisis Exploratorio (PASO 1 de la guía)
Genera: ML/01_eda_metricas.png  (grid 3×3 con 9 métricas)
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from common import load_acp, ML_OUT

# === 1. Carga y diagnóstico ===
df = load_acp()
print("=== DIAGNÓSTICO ACP ===")
print(f"Shape: {df.shape}")
print(f"Dtypes:\n{df.dtypes}")
print(f"Nulls:\n{df.isnull().sum()}")
print(f"Describe:\n{df.describe()}")

# === 2. Insights ===
print("\n=== INSIGHTS ===")
print("COVID dip 2020: tránsitos bajan respecto a 2019")
print("NeoPanamax ingresos > Panamax ingresos")
print(f"panamax_chico_transitos = 0 siempre? {(df['panamax_chico_transitos'] == 0).all()}")

# === 3. Grid 3×3 ===
import matplotlib.pyplot as plt

# Calcular métricas por año (para plots de fila 1 y 2)
anio_cols = ['panamax_alto_transitos', 'panamax_chico_transitos', 'neopanamax_transitos']
transitos_cols = anio_cols
ingresos_cols = ['panamax_ingresos', 'neopanamax_ingresos']
toneladas_cols = ['panamax_toneladas', 'neopanamax_toneladas']
volumen_cols = ['panamax_volumen', 'neopanamax_volumen']

fig, axes = plt.subplots(3, 3, figsize=(18, 14))
fig.suptitle("EDA Métricas Canal de Panamá", fontsize=16, fontweight='bold')

# --- Fila 1: totales por año ---
by_year = df.groupby('anio')

# 1.1 Tránsitos totales por año
t = by_year[transitos_cols].sum().sum(axis=1)
axes[0,0].bar(t.index.astype(str), t.values, color='steelblue')
axes[0,0].set_title("Tránsitos Totales por Año")
axes[0,0].set_xlabel("Año")
axes[0,0].set_ylabel("Tránsitos")
axes[0,0].tick_params(axis='x', rotation=45)

# 1.2 Ingresos totales por año
inc = by_year[ingresos_cols].sum().sum(axis=1) / 1e9
axes[0,1].bar(inc.index.astype(str), inc.values, color='forestgreen')
axes[0,1].set_title("Ingresos Totales por Año (B USD)")
axes[0,1].set_xlabel("Año")
axes[0,1].set_ylabel("Miles de Millones USD")
axes[0,1].tick_params(axis='x', rotation=45)

# 1.3 Volumen total por año
vol = by_year[volumen_cols].sum().sum(axis=1) / 1e6
axes[0,2].bar(vol.index.astype(str), vol.values, color='darkorange')
axes[0,2].set_title("Volumen Total por Año (Millones TM)")
axes[0,2].set_xlabel("Año")
axes[0,2].set_ylabel("Millones TM")
axes[0,2].tick_params(axis='x', rotation=45)

# --- Fila 2 ---
# 2.1 Toneladas por año
ton = by_year[toneladas_cols].sum().sum(axis=1) / 1e6
axes[1,0].bar(ton.index.astype(str), ton.values, color='coral')
axes[1,0].set_title("Toneladas Netas por Año (Millones)")
axes[1,0].set_xlabel("Año")
axes[1,0].tick_params(axis='x', rotation=45)

# 2.2 Panamax vs NeoPanamax — Tránsitos por año
pam = by_year['panamax_alto_transitos'].sum()
npm = by_year['neopanamax_transitos'].sum()
x = pam.index.astype(str)
width = 0.35
axes[1,1].bar([xi for xi in x], pam.values, width=width, label='Panamax', color='steelblue')
axes[1,1].bar([xi for xi in x], npm.values, width=width, label='NeoPanamax', color='darkorange')
axes[1,1].set_title("Panamax vs NeoPanamax — Tránsitos")
axes[1,1].legend()
axes[1,1].tick_params(axis='x', rotation=45)

# 2.3 Panamax vs NeoPanamax — Ingresos por año
pam_i = by_year['panamax_ingresos'].sum() / 1e9
npm_i = by_year['neopanamax_ingresos'].sum() / 1e9
axes[1,2].bar([xi for xi in x], pam_i.values, width=width, label='Panamax', color='steelblue')
axes[1,2].bar([xi for xi in x], npm_i.values, width=width, label='NeoPanamax', color='darkorange')
axes[1,2].set_title("Panamax vs NeoPanamax — Ingresos (B USD)")
axes[1,2].legend()
axes[1,2].tick_params(axis='x', rotation=45)

# --- Fila 3: promedios mensuales ---
by_month = df.groupby('mes')

# 3.1 Promedio mensual tránsitos
t_month = by_month[transitos_cols].sum().mean(axis=1)
month_order = list(range(1,13))
t_vals = [t_month.get(m, 0) for m in month_order]
axes[2,0].bar([f"E{F}" for F in range(1,13)], t_vals, color='steelblue')
axes[2,0].set_title("Promedio Mensual Tránsitos (2020-2025)")
axes[2,0].set_xlabel("Mes")

# 3.2 Promedio mensual ingresos
i_month = by_month[ingresos_cols].sum().mean(axis=1) / 1e9
i_vals = [i_month.get(m, 0) for m in month_order]
axes[2,1].bar([f"E{F}" for F in range(1,13)], i_vals, color='forestgreen')
axes[2,1].set_title("Promedio Mensual Ingresos (B USD)")
axes[2,1].set_xlabel("Mes")

# 3.3 Share NeoPanamax por año
pam_y = by_year['neopanamax_transitos'].sum()
npm_y = by_year['neopanamax_transitos'].sum() + by_year['panamax_alto_transitos'].sum()
share = (npm_y / (pam_y + npm_y) * 100).values
axes[2,2].plot(list(x), share, marker='o', color='darkorange', linewidth=2)
axes[2,2].set_title("% Trns. NeoPanamax sobre Total por Año")
axes[2,2].set_xlabel("Año")
axes[2,2].set_ylabel("%")
axes[2,2].tick_params(axis='x', rotation=45)

plt.tight_layout()
out_path = ML_OUT / "01_eda_metricas.png"
plt.savefig(out_path, dpi=150, bbox_inches='tight')
plt.close()
print(f"\n✅ Gráfico guardado: {out_path}")

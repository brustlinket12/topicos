"""
kmeans.py — Clustering de países con K-Means (PASO 9)
Genera: data/clusters_paises.csv (15 filas)
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from common import DATA_OUT, load_countries
import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

print("=== K-MEANS CLUSTERING DE PAÍSES ===")

# ============================================================
# 1. CARGAR DATOS
# ============================================================
df = load_countries()
print(f"Shape: {df.shape}")
print(f"Columnas: {list(df.columns)}")
print(df.head())

# Renombrar columnas a nombres limpios (snake_case)
# Columnas originales: País, Origen, Destino, Costa a Costa, Total,
#                      Total Menos Carga de Costa a Costa, %
col_map = {
    df.columns[0]: "pais",
    df.columns[1]: "origen",
    df.columns[2]: "destino",
    df.columns[3]: "costa_a_costa",
    df.columns[4]: "total",
    df.columns[5]: "total_menos_cc",
    df.columns[6]: "porcentaje",
}
df = df.rename(columns=col_map)

# Llenar NaN en costa_a_costa con 0
df["costa_a_costa"] = df["costa_a_costa"].fillna(0)
print(f"\nNulls tras fillna: {df['costa_a_costa'].isnull().sum()}")

# ============================================================
# 2. ESCALADO
# ============================================================
features = ["origen", "destino", "costa_a_costa", "total"]
X = df[features].values
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)
print(f"\nFeatures escaladas: {features}")

# ============================================================
# 3. K-MEANS
# ============================================================
km = KMeans(n_clusters=3, random_state=42, n_init=10)
df["cluster"] = km.fit_predict(X_scaled)

# Distancia a centroide
df["distancia_centroide"] = np.linalg.norm(
    X_scaled - km.cluster_centers_[df["cluster"]], axis=1
)

print(f"\nCluster centers (en espacio escalado):\n{km.cluster_centers_}")

# ============================================================
# 4. INTERPRETACIÓN
# ============================================================
print("\n=== INTERPRETACIÓN DE CLUSTERS ===")
for c in sorted(df["cluster"].unique()):
    subset = df[df["cluster"] == c].sort_values("total", ascending=False)
    print(f"\n--- Cluster {c} ({len(subset)} países) ---")
    print(f"  Total range: {subset['total'].min():,.0f} — {subset['total'].max():,.0f}")
    print(f"  Países: {', '.join(subset['pais'].tolist())}")

# ============================================================
# 5. EXPORTAR
# ============================================================
out_cols = ["pais", "origen", "destino", "costa_a_costa", "total",
            "total_menos_cc", "porcentaje", "cluster", "distancia_centroide"]
df_out = df[out_cols].copy()

out_path = DATA_OUT / "clusters_paises.csv"
df_out.to_csv(out_path, index=False, encoding="utf-8")
print(f"\n✅ Guardado: {out_path}")
print(f"   Filas: {len(df_out)}")

# Validación
assert len(df_out) == 15, f"Expected 15 rows, got {len(df_out)}"
assert set(df_out["cluster"].unique()).issubset({0, 1, 2}), "Clusters fuera de {0,1,2}!"
print("✅ Validación: 15 filas, clusters ∈ {0,1,2}")

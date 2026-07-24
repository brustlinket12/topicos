"""
export.py — Genera los 4 entregables finales para Power BI (PASOS 10-11)
  - data/fact_transitos.csv   (144 filas)
  - data/metricas_modelo.json (ganador por target + métricas completas)
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from common import load_acp, to_long, DATA_OUT, MODELS_OUT, ML_OUT
import pandas as pd
import json
import joblib
from datetime import datetime

print("=== EXPORT — ENTREGABLES POWER BI ===")

# ============================================================
# 1. fact_transitos.csv
# ============================================================
print("\n--- fact_transitos.csv ---")
df = load_acp()
df_long = to_long(df)

df_fact = df_long[["fecha", "segmento", "transitos", "ingresos", "toneladas", "volumen"]].copy()
# Formato ISO
df_fact["fecha"] = df_fact["fecha"].dt.strftime("%Y-%m-%d")

fact_path = DATA_OUT / "fact_transitos.csv"
df_fact.to_csv(fact_path, index=False, encoding="utf-8")
print(f"✅ Guardado: {fact_path}")
print(f"   Filas: {len(df_fact)} | Shape: {df_fact.shape}")
assert len(df_fact) == 144, f"Expected 144 rows, got {len(df_fact)}"
print("✅ Validación: 144 filas correctas")

# ============================================================
# 2. metricas_modelo.json
# ============================================================
print("\n--- metricas_modelo.json ---")

results = joblib.load(MODELS_OUT / "train_results.pkl")

def _metrics(sub_dict):
    return {
        "rmse": round(sub_dict["rmse"], 4),
        "r2":   round(sub_dict["r2"], 4),
        "mape": round(sub_dict["mape"], 2),
        "mae":  round(sub_dict["mae"], 2),
    }

metricas = {}
for target in ["ingresos", "transitos"]:
    r = results[target]
    winner = r["winner"]
    winner_key = "lr" if winner == "LinearRegression" else "rf"
    
    # Top-10 feature importance del RF
    fi = r["rf"]["feature_importance"]
    fi_sorted = dict(sorted(fi.items(), key=lambda x: x[1], reverse=True))
    top10 = {k: round(v, 6) for k, v in list(fi_sorted.items())[:10]}
    
    metricas[target] = {
        "linear_regression": _metrics(r["lr"]),
        "random_forest":     _metrics(r["rf"]),
        "ganador": winner,
    }
    
    # Agregar feature importance solo al target ingresos para el JSON
    # (evita duplicación, igual están ambas en fi de cada target)
    if target == "ingresos":
        metricas[target]["feature_importance_top10"] = top10

json_out = {
    "modelo_ganador_ingresos": results["ingresos"]["winner"],
    "modelo_ganador_transitos": results["transitos"]["winner"],
    "metricas": metricas,
    "feature_importance": {
        "ingresos_top10":  metricas["ingresos"].get("feature_importance_top10", {}),
        "transitos_top10": list(results["transitos"]["rf"]["feature_importance"].items())[:10],
    },
    "n_entrenamiento": results["ingresos"]["n_train"],
    "n_test":          results["ingresos"]["n_test"],
    "split_strategy":  "temporal 2020-01 a 2023-12 / 2024-01 a 2025-12",
    "fecha_entrenamiento": datetime.now().strftime("%Y-%m-%d"),
}

json_path = DATA_OUT / "metricas_modelo.json"
with open(json_path, "w", encoding="utf-8") as f:
    json.dump(json_out, f, indent=2, ensure_ascii=False)

print(f"✅ Guardado: {json_path}")
print(json.dumps(json_out, indent=2, ensure_ascii=False))

# Validaciones
assert "modelo_ganador_ingresos" in json_out
assert "modelo_ganador_transitos" in json_out
assert "rmse" in json_out["metricas"]["ingresos"]["random_forest"]
assert "feature_importance" in json_out
print("✅ Validación JSON: campos requeridos presentes")
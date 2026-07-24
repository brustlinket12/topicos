"""
predict_2026.py — Forecast recursivo 2026 (PASO 8)
Genera: data/predicciones_2026.csv (24 filas: 12 meses × 2 segmentos)
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from common import (
    load_acp, to_long, build_features, DATA_OUT, MODELS_OUT, ML_OUT,
    FEATURE_COLS, MONTHS_ES
)
import pandas as pd
import numpy as np
import joblib
from datetime import datetime

print("=== PREDICCIÓN 2026 — FORECAST RECURSIVO ===")

# ============================================================
# 1. CARGAR DATOS Y MODELOS
# ============================================================
df = load_acp()
df_long = to_long(df)

# Cargar train_results para saber el ganador por target
results = joblib.load(MODELS_OUT / "train_results.pkl")

# Cargar los modelos winners
modelos = {}
for target in ["ingresos", "transitos"]:
    winner_name = results[target]["winner"]
    if winner_name == "LinearRegression":
        modelos[target] = joblib.load(MODELS_OUT / f"lr_{target}.pkl")
    else:
        modelos[target] = joblib.load(MODELS_OUT / f"rf_{target}.pkl")
    print(f"  {target}: winner = {winner_name}")

# RMSE del ganador (para intervalos de confianza)
rmse_winner = {}
for target in ["ingresos", "transitos"]:
    winner_name = results[target]["winner"]
    key = "lr" if winner_name == "LinearRegression" else "rf"
    rmse_winner[target] = results[target][key]["rmse"]
    print(f"  RMSE winner ({target}): {rmse_winner[target]:.2f}")

# ============================================================
# 2. CONSTRUIR SEMILLA — últimas 12 filas reales por segmento
# ============================================================
df_feat_all = build_features(df_long)
segmentos = ["Panamax_AltoCalado", "NeoPanamax"]

# Para cada segmento: historial de los últimos 12 meses reales (2025)
semillas = {}
for seg in segmentos:
    seg_df = df_feat_all[df_feat_all["segmento"] == seg].tail(12).copy()
    seg_df = seg_df.sort_values("fecha")
    semillas[seg] = {
        "transitos_hist": seg_df["transitos"].tolist(),
        "anio": seg_df["anio"].tolist(),
        "mes_num": seg_df["mes_num"].tolist(),
    }
    print(f"\nSegmento {seg}: semilla de {seg_df['fecha'].min()} a {seg_df['fecha'].max()}")

# ============================================================
# 3. FORECAST RECURSIVO 2026
# ============================================================
predictions = []

for seg in segmentos:
    print(f"\n--- Forecast {seg} ---")
    
    # El último registro real (para calcular features)
    ultimo = df_feat_all[df_feat_all["segmento"] == seg].iloc[-1]
    
    # Reconstruir el historial completo para rolling
    transitos_hist = semillas[seg]["transitos_hist"].copy()
    anio_hist = semillas[seg]["anio"].copy()
    mes_hist = semillas[seg]["mes_num"].copy()
    
    for mes in range(1, 13):
        # --- Features temporales ---
        anio = 2026
        mes_num = mes
        trimestre = (mes_num - 1) // 3 + 1
        semestre = (mes_num - 1) // 6 + 1
        es_post_pandemia = 1
        
        # --- Lags ---
        transitos_lag1 = transitos_hist[-1] if len(transitos_hist) >= 1 else 0
        transitos_lag12 = transitos_hist[-12] if len(transitos_hist) >= 12 else transitos_hist[0]
        
        # --- Rolling means ---
        transitos_ma3 = np.mean(transitos_hist[-3:]) if len(transitos_hist) >= 3 else np.mean(transitos_hist)
        transitos_ma12 = np.mean(transitos_hist[-12:]) if len(transitos_hist) >= 12 else np.mean(transitos_hist)
        
        # --- Month dummies ---
        mes_dummies = {f"mes_{m}": 1 if mes_num == m else 0 for m in range(2, 13)}
        
        # --- Armar vector de features en orden de FEATURE_COLS ---
        feat_dict = {
            "anio": anio,
            "mes_num": mes_num,
            "trimestre": trimestre,
            "semestre": semestre,
            "es_post_pandemia": es_post_pandemia,
            "transitos_lag1": transitos_lag1,
            "transitos_lag12": transitos_lag12,
            "transitos_ma3": transitos_ma3,
            "transitos_ma12": transitos_ma12,
        }
        feat_dict.update(mes_dummies)
        
        X_pred = pd.DataFrame([[feat_dict[c] for c in FEATURE_COLS]], columns=FEATURE_COLS)
        
        # --- Predicción ---
        fecha = pd.Timestamp(f"2026-{mes:02d}-01")
        
        pred_ingresos = float(modelos["ingresos"].predict(X_pred)[0])
        pred_transitos = float(modelos["transitos"].predict(X_pred)[0])
        
        # --- Intervalos (solo para ingresos) ---
        rmse_ing = rmse_winner["ingresos"]
        lim_inf = pred_ingresos - 1.96 * rmse_ing
        lim_sup = pred_ingresos + 1.96 * rmse_ing
        
        # --- Guardar registro ---
        predictions.append({
            "fecha": fecha.strftime("%Y-%m-%d"),
            "segmento": seg,
            "pred_transitos": round(pred_transitos, 2),
            "pred_ingresos": round(pred_ingresos, 2),
            "limite_inferior": round(lim_inf, 2),
            "limite_superior": round(lim_sup, 2),
            "modelo": results["ingresos"]["winner"],
        })
        
        # --- Actualizar historial para próximo mes (bootstrap: la predicción alimenta lag1) ---
        transitos_hist.append(pred_transitos)
        anio_hist.append(2026)
        mes_hist.append(mes_num)
        
        print(f"  2026-{mes:02d} | {seg} | tránsitos={pred_transitos:.0f} | ingresos={pred_ingresos:.0f}")

# ============================================================
# 4. EXPORTAR
# ============================================================
df_pred = pd.DataFrame(predictions)
print(f"\n=== RESULTADO ===")
print(df_pred.to_string(index=False))

out_path = DATA_OUT / "predicciones_2026.csv"
df_pred.to_csv(out_path, index=False, encoding="utf-8")
print(f"\n✅ Guardado: {out_path}")

# Validación básica
assert len(df_pred) == 24, f"Expected 24 rows, got {len(df_pred)}"
assert (df_pred["pred_ingresos"] > 0).all(), "Hay ingresos <= 0!"
print("✅ Validación: 24 filas, todos pred_ingresos > 0")
"""
train.py — Entrenamiento LR + RF para ingresos Y tránsitos (PASOS 4-7)
Genera:
  ML/02_comparacion_modelos.png
  ML/03_feature_importance.png
  ML/models/lr_ingresos.pkl, rf_ingresos.pkl, lr_transitos.pkl, rf_transitos.pkl
  ML/models/train_results.pkl
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from common import (
    load_acp, to_long, build_features, temporal_split,
    MODELS_OUT, ML_OUT, mape, FEATURE_COLS
)
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import joblib

# ============================================================
# 1. CARGA Y FEATURES
# ============================================================
print("=== CARGANDO DATOS ===")
df = load_acp()
df_long = to_long(df)
print(f"df_long shape: {df_long.shape}")

df_feat = build_features(df_long)
print(f"df_feat shape (post dropna): {df_feat.shape}")
print(f"Features: {FEATURE_COLS}")

TARGETS = ["ingresos", "transitos"]
results = {}

for target in TARGETS:
    print(f"\n{'='*50}")
    print(f"  TARGET: {target}")
    print(f"{'='*50}")
    
    X_train, X_test, y_train, y_test, feat_cols = temporal_split(df_feat, target)
    print(f"Train: {X_train.shape[0]} | Test: {X_test.shape[0]}")
    
    # ============================================================
    # 2. LINEAR REGRESSION
    # ============================================================
    lr = LinearRegression()
    lr.fit(X_train, y_train)
    y_pred_lr_train = lr.predict(X_train)
    y_pred_lr_test  = lr.predict(X_test)
    
    rmse_lr = np.sqrt(mean_squared_error(y_test, y_pred_lr_test))
    mae_lr  = mean_absolute_error(y_test, y_pred_lr_test)
    r2_lr   = r2_score(y_test, y_pred_lr_test)
    mape_lr = mape(y_test, y_pred_lr_test)
    
    print(f"  LR — R²: {r2_lr:.4f} | RMSE: {rmse_lr:.2f} | MAE: {mae_lr:.2f} | MAPE: {mape_lr:.2f}%")
    
    # Coeficientes
    coef_sr = pd.Series(lr.coef_, index=feat_cols).sort_values()
    print(f"  Top 5 coefs LR:\n{coef_sr.tail(5)}")
    
    # ============================================================
    # 3. RANDOM FOREST
    # ============================================================
    rf = RandomForestRegressor(
        n_estimators=200,
        max_depth=10,
        random_state=42,
        n_jobs=-1
    )
    rf.fit(X_train, y_train)
    y_pred_rf_train = rf.predict(X_train)
    y_pred_rf_test  = rf.predict(X_test)
    
    rmse_rf = np.sqrt(mean_squared_error(y_test, y_pred_rf_test))
    mae_rf  = mean_absolute_error(y_test, y_pred_rf_test)
    r2_rf   = r2_score(y_test, y_pred_rf_test)
    mape_rf = mape(y_test, y_pred_rf_test)
    
    print(f"  RF — R²: {r2_rf:.4f} | RMSE: {rmse_rf:.2f} | MAE: {mae_rf:.2f} | MAPE: {mape_rf:.2f}%")
    
    # Importancias
    imp_sr = pd.Series(rf.feature_importances_, index=feat_cols).sort_values(ascending=False)
    print(f"  Top 10 features RF:\n{imp_sr.head(10)}")
    
    # ============================================================
    # 4. GANADOR POR RMSE
    # ============================================================
    winner = "LinearRegression" if rmse_lr < rmse_rf else "RandomForest"
    print(f"  🏆 Ganador ({target}): {winner} (RMSE {min(rmse_lr, rmse_rf):.2f})")
    
    # Guardar modelos
    joblib.dump(lr, MODELS_OUT / f"lr_{target}.pkl")
    joblib.dump(rf, MODELS_OUT / f"rf_{target}.pkl")
    
    results[target] = {
        "lr": {"rmse": rmse_lr, "mae": mae_lr, "r2": r2_lr, "mape": mape_lr,
               "y_test": y_test.values, "y_pred": y_pred_lr_test},
        "rf": {"rmse": rmse_rf, "mae": mae_rf, "r2": r2_rf, "mape": mape_rf,
               "y_test": y_test.values, "y_pred": y_pred_rf_test,
               "feature_importance": imp_sr.to_dict()},
        "winner": winner,
        "n_train": len(y_train),
        "n_test": len(y_test),
        "feature_cols": feat_cols,
        "X_train": X_train,
        "y_train": y_train,
        "X_test": X_test,
        "y_test": y_test,
    }

# Persistir resultados completos
joblib.dump(results, MODELS_OUT / "train_results.pkl")
print(f"\n✅ Modelos guardados en {MODELS_OUT}")

# ============================================================
# 5. GRÁFICOS
# ============================================================
print("\n=== GENERANDO GRÁFICOS ===")

# --- 02_comparacion_modelos.png: 2×2 scatter y_test vs y_pred ---
fig, axes = plt.subplots(2, 2, figsize=(14, 12))
fig.suptitle("Real vs Predicho — LR vs RF", fontsize=16, fontweight='bold')

positions = [
    (0, 0, "LR", "ingresos"),
    (0, 1, "RF", "ingresos"),
    (1, 0, "LR", "transitos"),
    (1, 1, "RF", "transitos"),
]

for ax_row, ax_col, model_name, target in positions:
    r = results[target]
    model_key = "lr" if model_name == "LR" else "rf"
    y_t = r[model_key]["y_test"]
    y_p = r[model_key]["y_pred"]
    rmse = r[model_key]["rmse"]
    r2   = r[model_key]["r2"]
    
    ax = axes[ax_row, ax_col]
    ax.scatter(y_t, y_p, alpha=0.6, edgecolors='k', linewidth=0.5)
    lims = [min(y_t.min(), y_p.min()), max(y_t.max(), y_p.max())]
    ax.plot(lims, lims, 'r--', linewidth=2, label='y=x ideal')
    ax.set_xlim(lims)
    ax.set_ylim(lims)
    ax.set_xlabel("Real")
    ax.set_ylabel("Predicho")
    ax.set_title(f"{model_name} — {target}\nR²={r2:.3f} RMSE={rmse:.0f}")
    ax.legend()

plt.tight_layout()
out1 = ML_OUT / "02_comparacion_modelos.png"
plt.savefig(out1, dpi=150, bbox_inches='tight')
plt.close()
print(f"✅ {out1}")

# --- 03_feature_importance.png: top-10 importancias RF por target ---
fig, axes = plt.subplots(2, 1, figsize=(12, 10))
fig.suptitle("Top 10 Feature Importance — Random Forest", fontsize=16, fontweight='bold')

for ax_idx, target in enumerate(["ingresos", "transitos"]):
    imp = pd.Series(results[target]["rf"]["feature_importance"]).sort_values()
    top10 = imp.tail(10)
    ax = axes[ax_idx]
    top10.plot(kind='barh', ax=ax, color='forestgreen')
    ax.set_title(f"Top 10 — {target}")
    ax.set_xlabel("Importancia")

plt.tight_layout()
out2 = ML_OUT / "03_feature_importance.png"
plt.savefig(out2, dpi=150, bbox_inches='tight')
plt.close()
print(f"✅ {out2}")

print("\n🎉 ENTRENAMIENTO COMPLETO")

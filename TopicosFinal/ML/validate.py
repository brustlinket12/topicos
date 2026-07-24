"""
validate.py — Validación final de los 4 entregables (PASO 12)
Ejecuta checks de contrato sobre los archivos de salida.
Exit code 0 = todos los checks pasan, 1 = algún fallo.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from common import DATA_OUT
import pandas as pd
import json
import sys as _sys

print("=" * 60)
print("  VALIDACION FINAL — ENTREGABLES POWER BI")
print("=" * 60)

checks = []
passed = 0
failed = 0

def check(name: str, condition: bool, detail: str = ""):
    global passed, failed
    status = "PASS" if condition else "FAIL"
    print(f"  [{status}] {name}" + (f" — {detail}" if detail else ""))
    checks.append({"name": name, "passed": condition, "detail": detail})
    if condition:
        passed += 1
    else:
        failed += 1

# ============================================================
# 1. fact_transitos.csv
# ============================================================
fact_path = DATA_OUT / "fact_transitos.csv"
check("fact_transitos.csv existe", fact_path.exists(), str(fact_path))

if fact_path.exists():
    df_fact = pd.read_csv(fact_path)
    check("fact_transitos: 144 filas", len(df_fact) == 144, f"got {len(df_fact)}")
    check("fact_transitos: columnas [fecha,segmento,transitos,ingresos,toneladas,volumen]",
          set(df_fact.columns) == {"fecha","segmento","transitos","ingresos","toneladas","volumen"},
          f"got {set(df_fact.columns)}")
    check("fact_transitos: fecha formato YYYY-MM-DD",
          df_fact["fecha"].str.match(r"\d{4}-\d{2}-\d{2}").all(),
          df_fact["fecha"].head(1).values[0])
    check("fact_transitos: transitos >= 0", (df_fact["transitos"] >= 0).all())
    check("fact_transitos: ingresos >= 0", (df_fact["ingresos"] >= 0).all())

# ============================================================
# 2. predicciones_2026.csv
# ============================================================
pred_path = DATA_OUT / "predicciones_2026.csv"
check("predicciones_2026.csv existe", pred_path.exists(), str(pred_path))

if pred_path.exists():
    df_pred = pd.read_csv(pred_path)
    check("predicciones_2026: 24 filas", len(df_pred) == 24, f"got {len(df_pred)}")
    check("predicciones_2026: 2 segmentos unicos",
          df_pred["segmento"].nunique() == 2,
          str(list(df_pred["segmento"].unique())))
    check("predicciones_2026: pred_ingresos > 0 todos",
          (df_pred["pred_ingresos"] > 0).all(),
          f"min={df_pred['pred_ingresos'].min():.2f}")
    check("predicciones_2026: sin nulos en columnas clave",
          df_pred[["fecha","segmento","pred_transitos","pred_ingresos"]].notna().all().all())
    check("predicciones_2026: limite inferior < limite superior",
          (df_pred["limite_inferior"] < df_pred["limite_superior"]).all())
    dentro = ((df_pred["pred_ingresos"] >= df_pred["limite_inferior"]) &
              (df_pred["pred_ingresos"] <= df_pred["limite_superior"])).all()
    check("predicciones_2026: pred_ingresos dentro del intervalo",
          dentro, "pred dentro de +/-1.96*RMSE")

# ============================================================
# 3. clusters_paises.csv
# ============================================================
clus_path = DATA_OUT / "clusters_paises.csv"
check("clusters_paises.csv existe", clus_path.exists(), str(clus_path))

if clus_path.exists():
    df_clus = pd.read_csv(clus_path)
    check("clusters_paises: 15 filas", len(df_clus) == 15, f"got {len(df_clus)}")
    check("clusters_paises: clusters en {0,1,2}",
          set(df_clus["cluster"].unique()).issubset({0, 1, 2}),
          f"got {set(df_clus['cluster'].unique())}")
    check("clusters_paises: columna distancia_centroide presente",
          "distancia_centroide" in df_clus.columns)

# ============================================================
# 4. metricas_modelo.json
# ============================================================
json_path = DATA_OUT / "metricas_modelo.json"
check("metricas_modelo.json existe", json_path.exists(), str(json_path))

if json_path.exists():
    with open(json_path, encoding="utf-8") as f:
        j = json.load(f)
    check("metricas: modelo_ganador_ingresos presente",
          "modelo_ganador_ingresos" in j)
    check("metricas: modelo_ganador_transitos presente",
          "modelo_ganador_transitos" in j)
    check("metricas: feature_importance presente",
          "feature_importance" in j)
    check("metricas: n_entrenamiento presente",
          "n_entrenamiento" in j)
    check("metricas: n_test presente",
          "n_test" in j)
    if "metricas" in j and "ingresos" in j["metricas"]:
        ing_rf = j["metricas"]["ingresos"].get("random_forest", {})
        check("metricas: rmse en random_forest_ingresos", "rmse" in ing_rf)
        check("metricas: r2 en random_forest_ingresos", "r2" in ing_rf)
        check("metricas: mape en random_forest_ingresos", "mape" in ing_rf)

# ============================================================
# RESUMEN
# ============================================================
print()
print("=" * 60)
print(f"  RESULTADO: {passed} PASS | {failed} FAIL")
print("=" * 60)
if failed == 0:
    print("  TODOS LOS CHECKS PASARON — ENTREGABLES LISTOS")
    _sys.exit(0)
else:
    print("  ALGUNOS CHECKS FALLARON — REVISAR ARRIBA")
    _sys.exit(1)

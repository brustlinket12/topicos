"""
common.py — Núcleo compartido del pipeline ML.
Todas las funciones de carga, transformación, paths y configuración
son centralizadas aquí para evitar duplicación entre scripts.
"""

from pathlib import Path
import pandas as pd
import numpy as np

# ==============================================================================
# PATHS — anclados al repo root (directorio que contiene ML/ y data/)
# ==============================================================================
REPO_ROOT = Path(__file__).resolve().parents[1]
ACP_CSV = REPO_ROOT / "A07607236202602121443442025_transporte_acp.csv"
COUNTRIES_CSV = REPO_ROOT / "Principales_Paises_Flujo_Carga_Canal_Panama.csv"
DATA_OUT = REPO_ROOT / "data"
ML_OUT = REPO_ROOT / "ML"
MODELS_OUT = ML_OUT / "models"

# Asegurar que las carpetas de salida existan
DATA_OUT.mkdir(exist_ok=True)
ML_OUT.mkdir(exist_ok=True)
MODELS_OUT.mkdir(exist_ok=True)

# ==============================================================================
# Nombres de columna objetivo (snake_case) — alineados por POSICIÓN
# El CSV tiene 11 columnas de datos + año + mes
# ==============================================================================
COLUMN_NAMES_TARGET = [
    "anio",                                    # 0 — columna "Año" en el CSV
    "mes",                                     # 1 — columna "Mes"
    "panamax_alto_transitos",                  # 2
    "panamax_chico_transitos",                 # 3
    "panamax_ingresos",                        # 4
    "panamax_toneladas",                       # 5
    "panamax_volumen",                         # 6
    "neopanamax_transitos",                    # 7
    "neopanamax_ingresos",                     # 8
    "neopanamax_toneladas",                    # 9
    "neopanamax_volumen",                      # 10
]

# ==============================================================================
# MESES EN ESPAÑOL — para parsear la columna `Mes`
# ==============================================================================
MONTHS_ES = {
    "Enero": 1,
    "Febrero": 2,
    "Marzo": 3,
    "Abril": 4,
    "Mayo": 5,
    "Junio": 6,
    "Julio": 7,
    "Agosto": 8,
    "Septiembre": 9,
    "Octubre": 10,
    "Noviembre": 11,
    "Diciembre": 12,
}

# ==============================================================================
# load_acp — Carga el CSV principal y renombra columnas
# ==============================================================================
def load_acp() -> pd.DataFrame:
    """
    Carga el CSV de transporte ACP con encoding 'latin-1'.
    Renombra las 11 columnas originales a snake_case en inglés POR POSICIÓN.
    Construye la columna 'fecha' como datetime (año + mes, día=1).
    Retorna DataFrame con 72 filas y 13 columnas.
    """
    df = pd.read_csv(ACP_CSV, encoding="latin-1", header=0)
    # Renombrar POR POSICIÓN para evitar problemas con caracteres rotos en los nombres
    df.columns = COLUMN_NAMES_TARGET
    df["fecha"] = pd.to_datetime(
        df["anio"].astype(str) + "-" + df["mes"].map(MONTHS_ES).astype(str) + "-01"
    )
    return df


# ==============================================================================
# to_long — reshape wide → long (formato largo para ML)
# ==============================================================================
def to_long(df: pd.DataFrame) -> pd.DataFrame:
    """
    Convierte el DataFrame wide (1 fila/mes) a formato largo
    (2 filas/mes: Panamax_AltoCalado + NeoPanamax).

    Columnas del resultado: fecha, segmento, transitos, ingresos,
                             toneladas, volumen

    Retorna DataFrame con 144 filas.
    """
    panamax = df[
        ["fecha", "anio", "mes", "panamax_alto_transitos",
         "panamax_ingresos", "panamax_toneladas", "panamax_volumen"]
    ].copy()
    panamax["segmento"] = "Panamax_AltoCalado"
    panamax = panamax.rename(
        columns={
            "panamax_alto_transitos": "transitos",
            "panamax_ingresos": "ingresos",
            "panamax_toneladas": "toneladas",
            "panamax_volumen": "volumen",
        }
    )

    neopanamax = df[
        ["fecha", "anio", "mes",
         "neopanamax_transitos", "neopanamax_ingresos",
         "neopanamax_toneladas", "neopanamax_volumen"]
    ].copy()
    neopanamax["segmento"] = "NeoPanamax"
    neopanamax = neopanamax.rename(
        columns={
            "neopanamax_transitos": "transitos",
            "neopanamax_ingresos": "ingresos",
            "neopanamax_toneladas": "toneladas",
            "neopanamax_volumen": "volumen",
        }
    )

    df_long = pd.concat([panamax, neopanamax], ignore_index=True)
    df_long = df_long.sort_values(["segmento", "fecha"]).reset_index(drop=True)
    return df_long


# ==============================================================================
# build_features — Ingeniería de features
# ==============================================================================
def build_features(df_long: pd.DataFrame) -> pd.DataFrame:
    """
    Añade features temporales, lags y rolling means por segmento.

    Features temporales: anio, mes_num, trimestre, semestre, es_post_pandemia
    Lags:         transitos_lag1 (1 mes), transitos_lag12 (12 meses)
    Rolling:      transitos_ma3 (media móvil 3 meses),
                  transitos_ma12 (media móvil 12 meses)
    Dummies:       mes_1 … mes_11  (diciembre = referencia, excluido)

    dropna() elimina las primeras 12 filas por los lags/rolling.
    Retorna ~120 filas.
    """
    df = df_long.copy()
    df = df.sort_values(["segmento", "fecha"]).reset_index(drop=True)

    # --- Features temporales ---
    df["anio"] = df["fecha"].dt.year
    df["mes_num"] = df["fecha"].dt.month
    df["trimestre"] = df["fecha"].dt.quarter
    df["semestre"] = (df["mes_num"] - 1) // 6 + 1
    df["es_post_pandemia"] = (df["anio"] >= 2021).astype(int)

    # --- Lags por segmento ---
    df["transitos_lag1"] = df.groupby("segmento")["transitos"].shift(1)
    df["transitos_lag12"] = df.groupby("segmento")["transitos"].shift(12)

    # --- Rolling means por segmento ---
    df["transitos_ma3"] = (
        df.groupby("segmento")["transitos"]
        .transform(lambda s: s.rolling(3, min_periods=3).mean())
    )
    df["transitos_ma12"] = (
        df.groupby("segmento")["transitos"]
        .transform(lambda s: s.rolling(12, min_periods=12).mean())
    )

    # --- Month dummies (diciembre como referencia → excluido) ---
    month_dummies = pd.get_dummies(df["mes_num"], prefix="mes", drop_first=True)
    # Asegurar que existen las 11 columnas mes_2 … mes_12 aunque haya meses sin datos
    for m in range(2, 13):
        col = f"mes_{m}"
        if col not in month_dummies.columns:
            month_dummies[col] = 0
    month_dummies = month_dummies.reindex(sorted(month_dummies.columns), axis=1)
    df = pd.concat([df, month_dummies], axis=1)

    # --- dropna ---
    df = df.dropna().reset_index(drop=True)
    return df


# ==============================================================================
# FEATURES — lista de columnas usadas como X (20 features)
# ==============================================================================
FEATURE_COLS = [
    # 5 temporales
    "anio", "mes_num", "trimestre", "semestre", "es_post_pandemia",
    # 4 lags/rolling
    "transitos_lag1", "transitos_lag12", "transitos_ma3", "transitos_ma12",
    # 11 dummies (mes_2 … mes_12, diciembre excluido)
    "mes_2", "mes_3", "mes_4", "mes_5", "mes_6",
    "mes_7", "mes_8", "mes_9", "mes_10", "mes_11", "mes_12",
]

# ==============================================================================
# temporal_split — Split temporal riguroso (SIN random split)
# ==============================================================================
def temporal_split(
    df: pd.DataFrame, target: str = "ingresos"
) -> tuple:
    """
    Divide el DataFrame en train (antes de 2024) y test (2024 en adelante).

    Params:
        df: DataFrame con features ya construidas (build_features)
        target: columna objetivo ('ingresos' o 'transitos')

    Returns:
        X_train, X_test, y_train, y_test, feature_names
    """
    train_mask = df["fecha"] < "2024-01-01"
    test_mask = df["fecha"] >= "2024-01-01"

    X_train = df.loc[train_mask, FEATURE_COLS]
    X_test = df.loc[test_mask, FEATURE_COLS]
    y_train = df.loc[train_mask, target]
    y_test = df.loc[test_mask, target]

    return X_train, X_test, y_train, y_test, FEATURE_COLS


# ==============================================================================
# MAPE — Mean Absolute Percentage Error (seguro contra /0)
# ==============================================================================
def mape(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Mean Absolute Percentage Error como porcentaje."""
    y_true = np.array(y_true)
    y_pred = np.array(y_pred)
    mask = y_true != 0
    return float(np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100)


# ==============================================================================
# Cargar países para K-Means
# ==============================================================================
def load_countries() -> pd.DataFrame:
    """
    Carga el CSV de países con encoding 'latin-1'.
    Retorna DataFrame con las columnas originales.
    """
    return pd.read_csv(COUNTRIES_CSV, encoding="latin-1")

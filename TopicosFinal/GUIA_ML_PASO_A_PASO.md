# Guía paso a paso: Machine Learning + Modelo Estrella para Canal de Panamá

> **Responsable de esta parte:** vos (Python/ML).  
> **Entregable final:** 4 archivos CSV limpios que alimentan el modelo estrella en Power BI.  
> **Alcance:** Regresión Lineal + Random Forest para predecir ingresos, K-Means para clustering de países.

---

## Archivos fuente

| Archivo | Ubicación | Descripción |
|---|---|---|
| `A07607236202602121443442025_transporte_acp.csv` | `TopicosFinal/` | 72 filas mensuales 2020–2025, 9 métricas (tránsitos, ingresos, toneladas por segmento) |
| `Principales_Paises_Flujo_Carga_Canal_Panama.csv` | `TOPICOS-CANAL/` | Top 15 países con flujo origen/destino/costa a costa |
| `P053342420251210083046Cuadro 34.csv` | `TopicosFinal/` | 11 filas trimestrales 2020–2024 (referencia, no usar para ML) |

---

## Estructura de carpetas a crear

```
TopicosFinal/
├── ML/
│   └── (tus scripts y notebooks)
└── data/
    ├── fact_transitos.csv          ← entregado por vos
    ├── predicciones_2026.csv      ← entregado por vos
    ├── clusters_paises.csv         ← entregado por vos
    └── metricas_modelo.json       ← entregado por vos
```

---

## PASO 0 — Preparar el entorno

1. Crear las carpetas `TopicosFinal/ML/` y `TopicosFinal/data/`.
2. Crear un entorno virtual (opcional pero recomendado):
   ```bash
   python -m venv venv
   .\venv\Scripts\activate   # Windows
   # source venv/bin/activate  # macOS/Linux
   ```
3. Instalar dependencias:
   ```bash
   pip install pandas numpy scikit-learn matplotlib seaborn openpyxls
   ```
4. Verificar encoding: al abrir el CSV en bloc de notas vas a ver `A?o` y `Peque?o` en vez de `Año` y `Pequeño`. Esto es **Latin-1**, no UTF-8.须.

---

## PASO 1 — Cargar y explorar (EDA)

### 1.1 Importar librerías
```python
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import json
import warnings
warnings.filterwarnings('ignore')
```

### 1.2 Cargar datos
```python
df = pd.read_csv(
    'TopicosFinal/A07607236202602121443442025_transporte_acp.csv',
    encoding='latin-1'
)
```

### 1.3 Explorar
```python
print("Shape:", df.shape)          # Esperás (72, 10)
print(df.dtypes)
print(df.isnull().sum())           # Verificar nulos
print(df.describe())
```

### 1.4 Inspección visual
- Esperás ver una caída fuerte en 2020 (COVID) y recuperación gradual.
- Los ingresos de NeoPanamax deberían ser consistentemente más altos que Panamax.
- `Transito de Naves Pequeño Calado Panamax` tiene muchos ceros → columna irrelevante para ML.

### 1.5 Guardar exploración
Generar 9 gráficos (uno por métrica) en un grid 3×3 con `plt.subplots()`. Guardar como `ML/01_eda_métricas.png`.

---

## PASO 2 — Limpieza y reestructuración

### 2.1 Renombrar columnas a snake_case en inglés
Crear un mapeo como este:

| Original (Latin-1) | Nuevo nombre |
|---|---|
| `A�o` | `año` |
| `Mes` | `mes` |
| `Transito de Naves Alto Calado Panamax` | `panamax_alto_transitos` |
| `Transito de Naves Peque�o Calado Panamax` | `panamax_chico_transitos` |
| `Ingresos por Peaje Panamax` | `panamax_ingresos` |
| `Toneladas Netas Panamax` | `panamax_toneladas` |
| `Volumen de Carga Panamax` | `panamax_volumen` |
| `Transito de Naves NeoPanamax` | `neopanamax_transitos` |
| `Ingresos por Peaje NeoPanamax` | `neopanamax_ingresos` |
| `Tonelada Netas Neopanamax` | `neopanamax_toneladas` |
| `Volumen de Carga NeoPanamax` | `neopanamax_volumen` |

### 2.2 Parsear fechas
```python
meses = {
    'Enero': 1, 'Febrero': 2, 'Marzo': 3, 'Abril': 4,
    'Mayo': 5, 'Junio': 6, 'Julio': 7, 'Agosto': 8,
    'Septiembre': 9, 'Octubre': 10, 'Noviembre': 11, 'Diciembre': 12
}
df['fecha'] = pd.to_datetime(df['año'].astype(str) + '-' + df['mes'].map(meses).astype(str) + '-01')
```

### 2.3 Formato long (recomendado para Power BI)
Convertir las 5 métricas principales (transitos, ingresos, toneladas, volumen) a formato largo, desdoblando Panamax y NeoPanamax:

```python
# Un ejemplo conceptual — ajustar según tu estructura final
filas = []
for _, row in df.iterrows():
    fecha = row['fecha']
    # Panamax Alto Calado
    filas.append({'fecha': fecha, 'segmento': 'Panamax_AltoCalado', 'transitos': row['panamax_alto_transitos'], 'ingresos': row['panamax_ingresos'], 'toneladas': row['panamax_toneladas'], 'volumen': row['panamax_volumen']})
    # NeoPanamax
    filas.append({'fecha': fecha, 'segmento': 'NeoPanamax', 'transitos': row['neopanamax_transitos'], 'ingresos': row['neopanamax_ingresos'], 'toneladas': row['neopanamax_toneladas'], 'volumen': row['neopanamax_volumen']})

df_long = pd.DataFrame(filas)
```

### 2.4 Validación
- `df_long.shape` debería dar (144, 7) → 72 meses × 2 segmentos.
- Sin nulos en las columnas numéricas.
- `fecha` en formato `datetime64[ns]`.

---

## PASO 3 — Feature Engineering

Crear las siguientes columnas en `df_long`. Estas son las **features** que van a entrar al modelo:

### 3.1 Features temporales
```python
df_long['año'] = df_long['fecha'].dt.year
df_long['mes_num'] = df_long['fecha'].dt.month
df_long['trimestre'] = df_long['fecha'].dt.quarter
df_long['semestre'] = (df_long['mes_num'] <= 6).astype(int) + 1
df_long['es_post_pandemia'] = (df_long['año'] >= 2022).astype(int)
```

### 3.2 Features de rezago (lags)
```python
# Lag 1: mes anterior
df_long = df_long.sort_values(['segmento', 'fecha'])
df_long['transitos_lag1'] = df_long.groupby('segmento')['transitos'].shift(1)

# Lag 12: mismo mes del año anterior
df_long['transitos_lag12'] = df_long.groupby('segmento')['transitos'].shift(12)

# Medias móviles
df_long['transitos_ma3'] = df_long.groupby('segmento')['transitos'].transform(lambda x: x.rolling(3, min_periods=1).mean())
df_long['transitos_ma12'] = df_long.groupby('segmento')['transitos'].transform(lambda x: x.rolling(12, min_periods=1).mean())
```

### 3.3 Dummies para estacionalidad
```python
# Una columna por mes (11 dummies, la 12ª queda como referencia)
for m in range(1, 12):
    df_long[f'mes_{m}'] = (df_long['mes_num'] == m).astype(int)
```

### 3.4 Dataset final para ML
```python
# Eliminar filas con NaN generados por los lags (los primeros 12 meses)
df_ml = df_long.dropna().copy()
print("Filas después de dropna:", df_ml.shape)  # Esperás ~120 filas
```

---

## PASO 4 — Train/Test Split temporal

**CRÍTICO:** NO usar `train_test_split` aleatorio. Para series de tiempo se parte en forma temporal:

| Período | Rango | Uso |
|---|---|---|
| Train | 2020-01 a 2023-12 | Entrenar |
| Test | 2024-01 a 2025-12 | Validar |

```python
train = df_ml[df_ml['fecha'] < '2024-01-01']
test  = df_ml[df_ml['fecha'] >= '2024-01-01']

feature_cols = [
    'transitos_lag1', 'transitos_lag12', 'transitos_ma3', 'transitos_ma12',
    'año', 'mes_num', 'trimestre', 'semestre', 'es_post_pandemia',
    'mes_1', 'mes_2', 'mes_3', 'mes_4', 'mes_5', 'mes_6',
    'mes_7', 'mes_8', 'mes_9', 'mes_10', 'mes_11'
]

X_train = train[feature_cols]
y_train = train['ingresos']
X_test  = test[feature_cols]
y_test  = test['ingresos']
```

---

## PASO 5 — Entrenar Modelo A (Regresión Lineal)

```python
lr = LinearRegression()
lr.fit(X_train, y_train)

# Predicciones
y_pred_lr = lr.predict(X_test)

# Coeficientes (para interpretabilidad)
coef_df = pd.DataFrame({
    'feature': feature_cols,
    'coeficiente': lr.coef_
}).sort_values('coeficiente', key=abs, ascending=False)

print("R² Train:", lr.score(X_train, y_train))
print("R² Test:", lr.score(X_test, y_test))
```

---

## PASO 6 — Entrenar Modelo B (Random Forest)

```python
rf = RandomForestRegressor(
    n_estimators=200,
    max_depth=10,
    random_state=42,
    n_jobs=-1
)
rf.fit(X_train, y_train)

# Predicciones
y_pred_rf = rf.predict(X_test)

# Feature importance
importance_df = pd.DataFrame({
    'feature': feature_cols,
    'importancia': rf.feature_importances_
}).sort_values('importancia', ascending=False)

print("R² Train:", rf.score(X_train, y_train))
print("R² Test:", rf.score(X_test, y_test))
```

---

## PASO 7 — Evaluar y comparar modelos

### 7.1 Calcular métricas en test set

```python
def calcular_metricas(y_true, y_pred, modelo_nombre):
    mae  = mean_absolute_error(y_true, y_pred)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    r2   = r2_score(y_true, y_pred)
    mape = np.mean(np.abs((y_true - y_pred) / y_true)) * 100

    print(f"\n=== {modelo_nombre} ===")
    print(f"MAE:  ${mae:,.0f}")
    print(f"RMSE: ${rmse:,.0f}")
    print(f"R²:   {r2:.4f}")
    print(f"MAPE: {mape:.1f}%")
    return {'mae': mae, 'rmse': rmse, 'r2': r2, 'mape': mape}

metricas_lr = calcular_metricas(y_test, y_pred_lr, "Regresión Lineal")
metricas_rf = calcular_metricas(y_test, y_pred_rf, "Random Forest")
```

### 7.2 Interpretación

| Métrica | Qué significa | Criterio de bondad |
|---|---|---|
| **MAE** | Error promedio en dólares | Cuanto menor, mejor |
| **RMSE** | Penaliza errores grandes | Cuanto menor, mejor |
| **R²** | Varianza explicada (0–1) | Más cerca de 1, mejor |
| **MAPE** | Error % promedio | < 10% = excelente, 10–20% = bueno |

### 7.3 Elegir modelo ganador
```python
if metricas_rf['rmse'] < metricas_lr['rmse']:
    mejor_modelo = 'RandomForest'
    print(f"Ganador: Random Forest (RMSE={metricas_rf['rmse']:,.0f})")
else:
    mejor_modelo = 'LinearRegression'
    print(f"Ganador: Regresión Lineal (RMSE={metricas_lr['rmse']:,.0f})")
```

### 7.4 Graficar comparación
Generar un chart con valores reales vs predichos para ambos modelos (2 líneas superpuestas). Guardar como `ML/02_comparacion_modelos.png`.

### 7.5 Graficar feature importance (Random Forest)
```python
plt.figure(figsize=(10, 6))
sns.barplot(data=importance_df.head(10), x='importancia', y='feature')
plt.title('Top 10 Feature Importance — Random Forest')
plt.tight_layout()
plt.savefig('ML/03_feature_importance.png')
plt.show()
```

---

## PASO 8 — Predicción 2026

### 8.1 Construir features para 2026
Necesitás generar las mismas features (lags, medias móviles, dummies) para los 12 meses de 2026. Esto requiere usar los últimos datos disponibles para calcular los lags:

```python
# Obtener último valor de la serie para calcular lags
ultimos = df_long.sort_values('fecha').groupby('segmento').tail(12)

# Construir DataFrame con fechas 2026
fechas_2026 = pd.date_range('2026-01-01', '2026-12-01', freq='MS')
segmentos = ['Panamax_AltoCalado', 'NeoPanamax']

preds_2026 = []
for seg in segmentos:
    ult_seg = ultimos[ultimos['segmento'] == seg].sort_values('fecha')
    ult_transitos = ult_seg['transitos'].values
    ult_ingresos  = ult_seg['ingresos'].values

    for i, fecha in enumerate(fechas_2026):
        lag1 = ult_transitos[-1] if i == 0 else None  # se actualiza iterativamente
        preds_2026.append({
            'fecha': fecha,
            'segmento': seg,
            'pred_transitos': pred_transito,
            'pred_ingresos': pred_ingreso,
            'limite_inferior': pred_ingreso - 1.96 * (metricas_rf['rmse']),
            'limite_superior': pred_ingreso + 1.96 * (metricas_rf['rmse'])
        })
```

> **Nota de implementación:** el cálculo real de lags para 2026 es iterativo — cada predicción del mes t se usa como input para el mes t+1. Usar el último valor conocido de la serie para bootstrap.

### 8.2 Exportar predicciones
```python
df_preds = pd.DataFrame(preds_2026)
df_preds['modelo'] = mejor_modelo
df_preds.to_csv('TopicosFinal/data/predicciones_2026.csv', index=False)
print("Predicciones 2026 exportadas:", df_preds.shape)
```

---

## PASO 9 — K-Means: Clustering de países

### 9.1 Cargar y limpiar datos de países
```python
df_paises = pd.read_csv(
    'TOPICOS-CANAL/Principales_Paises_Flujo_Carga_Canal_Panama.csv',
    encoding='latin-1'
)

# Renombrar columnas
df_paises.columns = ['pais', 'origen', 'destino', 'costa_a_costa', 'total', 'total_sin_costa', 'porcentaje']

# Llenar nulos de costa_a_costa con 0
df_paises['costa_a_costa'] = df_paises['costa_a_costa'].fillna(0)
```

### 9.2 Seleccionar features y estandarizar
```python
X_paises = df_paises[['origen', 'destino', 'costa_a_costa', 'total']].values
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X_paises)
```

### 9.3 Entrenar K-Means con k=3
```python
kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
df_paises['cluster'] = kmeans.fit_predict(X_scaled)

# Distancia al centroide
distancias = kmeans.transform(X_scaled)
df_paises['distancia_centroide'] = distancias[np.arange(len(df_paises)), df_paises['cluster']]
```

### 9.4 Interpretar clusters
```python
print(df_paises.groupby('cluster')[['origen', 'destino', 'total']].mean())
```

Ejemplo de interpretación esperada:
- **Cluster 0** (alto flujo): Estados Unidos, China, Japón.
- **Cluster 1** (medio flujo): Chile, Corea del Sur, Perú, México.
- **Cluster 2** (bajo flujo): resto.

### 9.5 Exportar
```python
df_paises.to_csv('TopicosFinal/data/clusters_paises.csv', index=False)
print("Clusters exportados:", df_paises.shape)
```

---

## PASO 10 — Generar metricas_modelo.json

```python
metricas_json = {
    "modelo_ganador": mejor_modelo,
    "rmse": float(metricas_rf['rmse']),
    "r2": float(metricas_rf['r2']),
    "mape": float(metricas_rf['mape']),
    "rmse_lineal": float(metricas_lr['rmse']),
    "r2_lineal": float(metricas_lr['r2']),
    "mape_lineal": float(metricas_lr['mape']),
    "feature_importance": dict(zip(feature_cols, rf.feature_importances_.tolist())),
    "n_entrenamiento": len(X_train),
    "n_test": len(X_test)
}

with open('TopicosFinal/data/metricas_modelo.json', 'w') as f:
    json.dump(metricas_json, f, indent=2)
```

---

## PASO 11 — Exportar fact_transitos.csv

```python
# Seleccionar columnas finales
fact_cols = ['fecha', 'segmento', 'transitos', 'ingresos', 'toneladas', 'volumen']
df_fact = df_long[fact_cols].copy()
df_fact.to_csv('TopicosFinal/data/fact_transitos.csv', index=False)
print("Fact transitos exportado:", df_fact.shape)
```

---

## PASO 12 — Validación final

Abrir cada archivo en Excel y verificar:

| Archivo | Qué verificar |
|---|---|
| `fact_transitos.csv` | 144 filas, sin nulos, `fecha` en formato `YYYY-MM-DD` |
| `predicciones_2026.csv` | 24 filas (2 segmentos × 12 meses), `pred_ingresos` positivo |
| `clusters_paises.csv` | 15 filas, columna `cluster` con valores 0, 1, 2 |
| `metricas_modelo.json` | Campos `modelo_ganador`, `rmse`, `r2`, `mape` presentes |

---

## Checklist de entrega

- [ ] Carpetas `ML/` y `data/` creadas
- [ ] `fact_transitos.csv` en `TopicosFinal/data/`
- [ ] `predicciones_2026.csv` en `TopicosFinal/data/`
- [ ] `clusters_paises.csv` en `TopicosFinal/data/`
- [ ] `metricas_modelo.json` en `TopicosFinal/data/`
- [ ] Gráficos `01_eda_métricas.png`, `02_comparacion_modelos.png`, `03_feature_importance.png` en `ML/`
- [ ] Ningún archivo tiene tildes rotas ni caracteres extraños
- [ ] Los 4 CSV están en encoding UTF-8 (verificar con `file` o abriéndolos en bloc de notas)

---

## Consejos para la defensa oral

1. **¿Por qué no aleatorio el split?** → "Porque estamos ante serie temporal. Mezclar fechas rompe la estructura temporal y genera data leakage."
2. **¿Por qué no redes neuronales?** → "Con 60-70 puntos de entrenamiento, una red neuronal sobreajusta. Los modelos simples generalizan mejor."
3. **¿Por qué dos modelos?** → "Compara interpretabilidad (regresión lineal) vs. performance (Random Forest). Elijimos por RMSE."
4. **¿Qué pasa si gana la regresión lineal?** → "Es válido. A veces datos pequeños favorecen modelos simples. Lo importante es justificar la decisión con datos."
5. **¿Por qué K-Means y no jerárquico?** → "Tenés un número自然的 de clusters (alto/medio/bajo flujo), entonces K-Means es más directo."

---

## Próximo paso

Cuando termines, avisa y paso a construir el modelo estrella en Power BI Desktop usando los 4 archivos que me entregás.

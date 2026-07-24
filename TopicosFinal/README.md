# Proyecto TopicosFinal - Análisis del Canal de Panamá

## Descripción del Proyecto

Este proyecto desarrolla un sistema de análisis de datos y Machine Learning para el **Canal de Panamá**, incluyendo:

- Análisis histórico de tránsitos e ingresos (2020-2025)
- Predicciones de tráfico para 2026 mediante modelos de Machine Learning
- Clusterización de países por patrones de tráfico
- Dashboard interactivo en Power BI con modelo estrella

---

## Estructura del Proyecto

```
TopicosFinal/
├── data/                                    # Datos limpios
│   ├── fact_transitos.csv                   # Histórico mensual 2020-2025 (144 filas)
│   ├── predicciones_2026.csv                # Predicciones ML 2026 (24 filas)
│   ├── clusters_paises.csv                   # K-Means 15 países (3 clusters)
│   ├── metricas_planas.csv                  # 14 métricas de modelo en formato largo
│   ├── feature_importance.csv               # Top 10 features por target (20 filas)
│   └── metricas_modelo.json                # Métricas completas (referencia)
│
├── powerbi/                                 # Archivos de Power BI
│   ├── Canal_Panama_Analytics.pbix           # Reporte principal (entregable)
│   ├── theme_institucional.json              # Tema azul/gris
│   ├── queries_power_query.m                 # Código M para transformaciones
│   ├── medidas_dax.txt                       # 22 medidas DAX documentadas
│   └── INSTRUCCIONES_PASO_A_PASO.md         # Guía de armado del .pbix
│
├── ML/                                       # Pipeline de Machine Learning
│   ├── train.py                              # Entrenamiento de modelos
│   ├── predict_2026.py                       # Generación de predicciones
│   ├── kmeans.py                             # Clusterización de países
│   ├── eda.py                                # Análisis exploratorio
│   ├── export.py                             # Exportación a CSV
│   ├── validate.py                           # Validación
│   ├── common.py                             # Utilidades compartidas
│   ├── 01_eda_metricas.png                   # Gráfico EDA
│   ├── 02_comparacion_modelos.png            # Comparación LR vs RF
│   ├── 03_feature_importance.png             # Importancia de variables
│   ├── models/                               # Modelos entrenados (.pkl)
│   │   ├── lr_ingresos.pkl
│   │   ├── lr_transitos.pkl
│   │   ├── rf_ingresos.pkl
│   │   └── rf_transitos.pkl
│   └── __pycache__/                          # Cache Python
│
├── pipeline.ipynb                            # Notebook completo del pipeline
├── GUIA_ML_PASO_A_PASO.md                    # Guía de la fase de ML
├── recomendaciones.txt                       # Notas de ML
├── requirements.txt                          # Dependencias Python
├── P053342420251210083046Cuadro 34.csv       # Datos trimestrales ACP
├── A07607236202602121443442025_transporte_acp.csv  # Datos mensuales ACP
└── README.md                                 # Este archivo
```

---

## Fuentes de Datos

### 1. fact_transitos.csv (144 filas)
Datos mensuales de tránsitos por segmento del Canal de Panamá.

| Columna | Descripción | Tipo |
|---------|-------------|------|
| fecha | Fecha (YYYY-MM-01) | date |
| segmento | NeoPanamax / Panamax_AltoCalado | text |
| transitos | Número de buques que transitaron | integer |
| ingresos | Ingresos en USD | integer |
| toneladas | Carga en toneladas | integer |
| volumen | Volumen en metros cúbicos | integer |

**Período**: Enero 2020 - Diciembre 2025

### 2. predicciones_2026.csv (24 filas)
Predicciones de tránsitos e ingresos para 2026 con intervalos de confianza.

| Columna | Descripción | Tipo |
|---------|-------------|------|
| fecha | Fecha (YYYY-MM-01) | date |
| segmento | NeoPanamax / Panamax_AltoCalado | text |
| pred_transitos | Predicción de tránsitos | float |
| pred_ingresos | Predicción de ingresos (USD) | float |
| limite_inferior | IC 95% inferior | float |
| limite_superior | IC 95% superior | float |
| modelo | Modelo utilizado | text |

### 3. clusters_paises.csv (15 países)
Clusterización K-Means de países según patrones de tráfico.

| Columna | Descripción | Tipo |
|---------|-------------|------|
| pais | Nombre del país | text |
| origen | Tráfico de origen (toneladas) | integer |
| destino | Tráfico de destino (toneladas) | integer |
| costa_a_costa | Tráfico costa a costa | float |
| total | Tráfico total | integer |
| cluster | ID del cluster (0, 1, 2) | integer |
| distancia_centroide | Distancia al centroide | float |

**Clusters identificados**:
- **Cluster 1 - Alto flujo**: Estados Unidos
- **Cluster 0 - Medio flujo**: Chile, Corea del Sur, Perú, México, Colombia, Ecuador, Canadá, Panamá, Guatemala, Brasil, España, Holanda
- **Cluster 2 - Bajo flujo**: China, Japón

### 4. metricas_planas.csv y feature_importance.csv
Versiones planas (1 fila por métrica / feature) para importación limpia a Power BI.

---

## Modelos de Machine Learning

### Modelos Comparados
1. **Linear Regression** ✅ Ganador
2. **Random Forest** ❌ Descartado por sobreajuste (R² negativo en ingresos)

### Features Utilizados (Top 10)
1. `transitos_lag1` - Tránsitos del mes anterior
2. `transitos_ma3` - Promedio móvil 3 meses
3. `transitos_ma12` - Promedio móvil 12 meses
4. `transitos_lag12` - Mismo mes año anterior
5. `anio` - Tendencia anual
6. `mes_num` - Estacionalidad mensual
7. `trimestre` - Estacionalidad trimestral
8. `mes_9`, `mes_7`, `mes_2` - Dummies de mes

### Resultados (Linear Regression - ganador)

| Métrica | Tránsitos | Ingresos |
|---------|-----------|----------|
| R² | 0.9771 | 0.6928 |
| RMSE | 32.51 | 14,774,370 |
| MAE | 25.14 | 11,639,196 |
| **MAPE** | **6.74%** | **7.9%** |

### Estrategia de Validación
- **Entrenamiento**: 2020-01 a 2023-12 (48 meses)
- **Test**: 2024-01 a 2025-12 (24 meses)
- **Split**: Temporal (sin shuffle, preserva orden cronológico)

---

## Dashboard de Power BI

El archivo `powerbi/Canal_Panama_Analytics.pbix` contiene un reporte con 4 páginas:

### Página 1: Resumen Ejecutivo
- 6 KPI cards (MAPE, predicción 2026, yield, ingresos, variación YoY, tránsitos)
- Línea de tendencia con histórico + predicción
- Tabla de métricas del modelo
- Slicers de segmento y año

### Página 2: Análisis por Segmento
- 5 KPI cards por segmento
- Bar chart agrupado 2024 vs 2025
- Treemap de participación
- Tabla resumen

### Página 3: Análisis Geográfico
- Mapa coroplético por país
- Treemap Origen vs Destino
- Scatter con clusters
- Tabla de 15 países

### Página 4: Predicciones & IA
- 4 cards de métricas del modelo
- Línea con intervalo de confianza
- Tabla de predicciones mes a mes
- Bar chart de feature importance
- Smart Narrative (placeholder para LLM)

### Modelo Estrella (Star Schema)
- **Dim_Calendario** (Date, Año, Mes, Trimestre, Semestre) → `fact_transitos` (1:*)
- **Dim_Calendario** → `predicciones_2026` (1:*)
- 22 medidas DAX (operativas, temporales, predictivas, top)

---

## Guía de Implementación

### Power BI (recomendado)
1. Abrir `powerbi/Canal_Panama_Analytics.pbix` con Power BI Desktop
2. Si los mapas no se ven: Archivo → Opciones → Global → Seguridad → tildar "Usar objetos visuales de mapa"
3. Si querés reconstruirlo: seguir `powerbi/INSTRUCCIONES_PASO_A_PASO.md`

### Python / Jupyter
1. Instalar dependencias: `pip install -r requirements.txt`
2. Ejecutar `pipeline.ipynb` para regenerar todos los datos
3. O ejecutar módulos individuales en `ML/`

---

## Requisitos

### Python
```
pandas>=2.0
numpy>=1.24
scikit-learn>=1.3
matplotlib>=3.7
seaborn>=0.12
openpyxl>=3.1
joblib>=1.3
```

### Power BI
- Power BI Desktop (versión reciente)
- Habilitar mapas: Archivo → Opciones → Global → Seguridad
- Habilitar scripts de Python (opcional, para visualizaciones avanzadas)

---

## Metodología

Este proyecto sigue la metodología **CRISP-DM** (Cross-Industry Standard Process for Data Mining):

1. **Comprensión del Negocio**: Análisis del dominio del Canal de Panamá
2. **Comprensión de los Datos**: EDA, detección de patrones
3. **Preparación de Datos**: Limpieza, encoding, feature engineering
4. **Modelado**: Entrenamiento y comparación de modelos
5. **Evaluación**: Validación con métricas estándar (RMSE, MAE, R², MAPE)
6. **Despliegue**: Exportación a CSV + dashboard Power BI

---

## Pendiente

- **Integración LLM**: Página 4 del dashboard tiene un Smart Narrative como placeholder. La integración con un LLM (OpenAI, Ollama, etc.) será completada por otro integrante del equipo.

---

## Autor y Fecha

- **Proyecto**: TopicosFinal - Análisis del Canal de Panamá
- **Fecha**: Julio 2026
- **Datos históricos**: 2020-2025
- **Predicciones**: 2026
- **Stack**: Python (scikit-learn, pandas) + Power BI Desktop
- **Metodología**: CRISP-DM

---

## Licencia y Uso

Este proyecto fue desarrollado con fines educativos y de análisis. Los datos del Canal de Panamá son propiedad de la Autoridad del Canal de Panamá (ACP).

---

## Enlaces de Interés

- [Documentación de Power BI](https://docs.microsoft.com/es-es/power-bi/)
- [Referencia DAX](https://docs.microsoft.com/es-es/dax/)
- [Power Query M Reference](https://docs.microsoft.com/es-es/power-query-m/)
- [scikit-learn Documentation](https://scikit-learn.org/stable/)

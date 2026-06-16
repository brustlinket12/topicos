# Panama Canal Data Dashboard

## Objetivo

Dashboard interactivo en Streamlit que visualiza y analiza los datos de tránsitos y carga del Canal de Panamá, incluyendo comparativas 2024 vs 2025, rankings por país, y predicciones para 2026 mediante regresión lineal.

## PRD Requirements Checklist

- [x] KPI cards: total tránsitos 2024, 2025, variación %, segmento mayor crecimiento, segmento mayor caída, país top, predicción 2026
- [x] Bar chart agrupado: Tránsitos 2024 vs 2025 por segmento (Plotly)
- [x] Bar chart: % Diferencia Tránsitos por segmento (Plotly)
- [x] Bar chart horizontal: Top países por Total (Plotly)
- [x] Choropleth map: países por volumen de carga (Plotly)
- [x] Prediction bar chart: predicción 2026 por segmento
- [x] Resumen ejecutivo con OpenRouter + fallback automático
- [x] Sidebar con API key (password), selector de modelo, botón generar
- [x] @st.cache_data para carga de CSVs y entrenamiento del modelo
- [x] Sin API keys hardcodeadas — variables de entorno o sidebar

## Data Sources

- `Principales_Paises_Flujo_Carga_Canal_Panama.csv` — volumen de carga por país
- `Trafico_Buques_Segmento_Mercado_Canal_Panama.csv` — tránsitos por segmento de mercado

## File Structure

```
TOPICOS-CANAL/
├── app.py                                          # Streamlit dashboard
├── pipeline.ipynb                                  # Jupyter notebook (análisis original)
├── requirements.txt                               # Dependencias Python
├── Principales_Paises_Flujo_Carga_Canal_Panama.csv
├── Trafico_Buques_Segmento_Mercado_Canal_Panama.csv
├── tendencia_transitos.png                         # Output notebook
├── variacion_tendencia.png                        # Output notebook
├── top_paises.png                                  # Output notebook
├── prediccion_2026.png                            # Output notebook
└── explicacion/                                    # Documentación del notebook
```

## Installation

```bash
pip install -r requirements.txt
```

## Notebook Execution

```bash
cd TOPICOS-CANAL
jupyter nbconvert --execute pipeline.ipynb --to notebook --inplace
```

## Dashboard Execution

```bash
cd TOPICOS-CANAL
streamlit run app.py
```

## OpenRouter Configuration

La API key puede configurarse de dos formas:

1. **Variable de entorno** (recomendado para producción):
   ```bash
   export OPENROUTER_API_KEY=sk-or-...
   export OPENROUTER_MODEL=nvidia/nemotron-3-ultra-550b-a55b:free
   streamlit run app.py
   ```

2. **Sidebar** (ingreso manual en la interfaz):
   - Abrir dashboard
   - Ingresar OPENROUTER_API_KEY en el campo de la barra lateral
   - Opcionalmente cambiar el modelo
   - Click "Generar resumen"

## Model

- **Default**: `nvidia/nemotron-3-ultra-550b-a55b:free`
- Compatible con cualquier modelo OpenRouter (OpenAI-compatible)

## Model Limitations Disclaimer

- La predicción 2026 utiliza **regresión lineal simple** entrenada con datos 2024→2025
- No captura estacionalidad, eventos geopolíticos, ni cambios estructurales
- Es una estimación orientativa, **no una garantía** de resultados futuros
- El modelo puede tener errores significativos para segmentos con cambios abruptos

## Fallback Behavior

Si no se proporciona API key o la llamada a OpenRouter falla, el dashboard muestra un resumen automático predefinido que incluye los KPIs principales. El dashboard es completamente funcional sin API key.

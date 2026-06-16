# AGENTS.md

## Project Shape
- Active project lives in `TOPICOS-CANAL/`; the workspace root only contains `.git/`, this file, and that project directory.
- Main entrypoint is `TOPICOS-CANAL/pipeline.ipynb`, a Jupyter notebook that reads two CSV files from its current working directory and regenerates PNG charts.
- Data inputs are `Principales_Paises_Flujo_Carga_Canal_Panama.csv` and `Trafico_Buques_Segmento_Mercado_Canal_Panama.csv`.
- Generated/checked-in outputs are `tendencia_transitos.png`, `variacion_tendencia.png`, `top_paises.png`, and `prediccion_2026.png`.
- `TOPICOS-CANAL/explicacion` is prose explaining notebook cells; keep it aligned if notebook logic changes.

## Tooling
- No `package.json`, lockfile, CI workflow, formatter, linter, test config, or Python requirements file exists in this repo.
- Notebook dependencies observed in `pipeline.ipynb`: `pandas`, `matplotlib`, `scikit-learn`, and `numpy`.
- If dependencies are missing, install from the project environment with `python -m pip install pandas matplotlib scikit-learn`; `numpy` is pulled by these dependencies but is imported directly.
- The notebook metadata records Python `3.11.9` / kernel `python3`.

## Run And Verify
- Run notebook cells from `TOPICOS-CANAL/` so relative CSV paths resolve.
- For CLI execution, use `jupyter nbconvert --execute pipeline.ipynb --to notebook --inplace` from `TOPICOS-CANAL/`; this updates notebook outputs and may rewrite metadata.
- There are no automated tests. Verification is: notebook runs without exceptions and regenerates the four PNG files above.

## Editing Notes
- Do not rename CSV columns casually; the notebook indexes Spanish column names exactly, including accents: `País`, `Tránsitos 2024`, `Tránsitos 2025`, `% Diferencia Tránsitos`, and `Segmento de Mercado`.
- The notebook removes the `Total` row from `Segmento de Mercado` before analysis; preserve this unless changing the analysis intent.
- Percentage columns arrive as strings like `15.63%`; convert or strip `%` before numeric operations.
- Some CSV numeric fields are blank and are treated as missing values; current notebook fills selected columns with `0` before plotting/modeling.
- Do not run a build for this repo; none exists.

## Streamlit Dashboard

- `TOPICOS-CANAL/app.py` es el dashboard Streamlit.
- Ejecutar desde `TOPICOS-CANAL/`: `streamlit run app.py`
- Variables de entorno: `OPENROUTER_API_KEY`, `OPENROUTER_MODEL` (default: `nvidia/nemotron-3-ultra-550b-a55b:free`)
- API keys **nunca hardcodearas** — usar `os.getenv` o el sidebar.
- Sin API key funciona con resumen automático de fallback.
- Verificación: `streamlit run app.py` abre sin errores.
- Dependencias: `requirements.txt` (pandas, numpy, matplotlib, scikit-learn, streamlit, plotly, openai, requests)

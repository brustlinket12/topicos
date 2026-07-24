from __future__ import annotations

import json
import os
from pathlib import Path

import pandas as pd
import plotly.express as px
import requests
import streamlit as st


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DEFAULT_MODEL = os.getenv(
    "OPENROUTER_MODEL",
    "nvidia/nemotron-3-ultra-550b-a55b:free",
)


@st.cache_data
def load_data() -> dict[str, object]:
    historical = pd.read_csv(DATA_DIR / "fact_transitos.csv", parse_dates=["fecha"])
    predictions = pd.read_csv(
        DATA_DIR / "predicciones_2026.csv", parse_dates=["fecha"]
    )
    countries = pd.read_csv(DATA_DIR / "clusters_paises.csv", encoding="utf-8-sig")
    features = pd.read_csv(DATA_DIR / "feature_importance.csv", encoding="utf-8-sig")
    metrics = json.loads((DATA_DIR / "metricas_modelo.json").read_text("utf-8"))
    return {
        "historical": historical,
        "predictions": predictions,
        "countries": countries,
        "features": features,
        "metrics": metrics,
    }


def compact_context(data: dict[str, object]) -> str:
    historical: pd.DataFrame = data["historical"]  # type: ignore[assignment]
    predictions: pd.DataFrame = data["predictions"]  # type: ignore[assignment]
    countries: pd.DataFrame = data["countries"]  # type: ignore[assignment]
    features: pd.DataFrame = data["features"]  # type: ignore[assignment]
    metrics: dict = data["metrics"]  # type: ignore[assignment]

    annual = (
        historical.assign(anio=historical["fecha"].dt.year)
        .groupby(["anio", "segmento"], as_index=False)[
            ["transitos", "ingresos", "toneladas", "volumen"]
        ]
        .sum()
    )
    pred_by_segment = predictions.groupby("segmento", as_index=False)[
        ["pred_transitos", "pred_ingresos"]
    ].sum()
    top_countries = countries.nlargest(10, "total")[
        ["pais", "origen", "destino", "total", "cluster"]
    ]
    top_features = features.nlargest(10, "importancia")

    return "\n\n".join(
        [
            "MÉTRICAS DEL MODELO:\n"
            + json.dumps(metrics, ensure_ascii=False, indent=2),
            "HISTÓRICO ANUAL POR SEGMENTO:\n"
            + annual.to_csv(index=False),
            "PREDICCIONES 2026 POR SEGMENTO:\n"
            + pred_by_segment.to_csv(index=False),
            "TOP 10 PAÍSES:\n" + top_countries.to_csv(index=False),
            "FEATURE IMPORTANCE:\n" + top_features.to_csv(index=False),
        ]
    )


def fallback_answer(question: str, data: dict[str, object]) -> str:
    historical: pd.DataFrame = data["historical"]  # type: ignore[assignment]
    predictions: pd.DataFrame = data["predictions"]  # type: ignore[assignment]
    countries: pd.DataFrame = data["countries"]  # type: ignore[assignment]
    metrics: dict = data["metrics"]  # type: ignore[assignment]

    total_transits = int(historical["transitos"].sum())
    total_income = float(historical["ingresos"].sum())
    pred_transits = float(predictions["pred_transitos"].sum())
    pred_income = float(predictions["pred_ingresos"].sum())
    leader = countries.nlargest(1, "total").iloc[0]
    lr = metrics["metricas"]["transitos"]["linear_regression"]

    return (
        "No hay una API key configurada, así que muestro un resumen calculado "
        "directamente de los datos:\n\n"
        f"- Histórico 2020–2025: **{total_transits:,.0f} tránsitos** y "
        f"**US${total_income / 1_000_000:,.1f} millones** en ingresos.\n"
        f"- Predicción 2026: **{pred_transits:,.0f} tránsitos** y "
        f"**US${pred_income / 1_000_000:,.1f} millones**.\n"
        f"- País con mayor flujo: **{leader['pais']}**, con "
        f"**{leader['total']:,.0f}** unidades de carga total.\n"
        f"- Modelo ganador para tránsitos: **LinearRegression**, "
        f"R² **{lr['r2']:.4f}** y MAPE **{lr['mape']:.2f}%**.\n\n"
        f"Pregunta recibida: “{question}”. Para una respuesta interpretativa "
        "específica, agrega `OPENROUTER_API_KEY` en el entorno o en la barra lateral."
    )


def ask_llm(
    question: str,
    history: list[dict[str, str]],
    context: str,
    api_key: str,
    model: str,
) -> str:
    system_prompt = f"""
Eres un analista del Canal de Panamá integrado en un dashboard de Power BI.
Responde en español, de forma clara, breve y basada únicamente en los datos
proporcionados. Distingue historia (2020-2025) de predicción (2026), indica
unidades y redondea cifras grandes. No inventes valores. Si la pregunta no puede
responderse con el contexto, dilo y sugiere qué dato falta.

CONTEXTO DE DATOS:
{context}
"""
    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(history[-8:])
    messages.append({"role": "user", "content": question})

    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:8501",
            "X-Title": "Canal de Panama Analytics",
        },
        json={
            "model": model,
            "messages": messages,
            "temperature": 0.2,
        },
        timeout=90,
    )
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]


st.set_page_config(
    page_title="Asistente Canal de Panamá",
    page_icon="🚢",
    layout="wide",
)

st.markdown(
    """
    <style>
    .stApp { background: #f4f7fb; }
    [data-testid="stMetric"] {
        background: white;
        border: 1px solid #dbe4ef;
        border-radius: 12px;
        padding: 14px;
    }
    [data-testid="stChatMessage"] {
        background: white;
        border: 1px solid #dbe4ef;
        border-radius: 14px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

data = load_data()
historical: pd.DataFrame = data["historical"]  # type: ignore[assignment]
predictions: pd.DataFrame = data["predictions"]  # type: ignore[assignment]

with st.sidebar:
    st.header("Configuración")
    api_key = st.text_input(
        "OpenRouter API key",
        value=os.getenv("OPENROUTER_API_KEY", ""),
        type="password",
        help="No se guarda en archivos ni se incluye en el reporte.",
    )
    model = st.text_input("Modelo", value=DEFAULT_MODEL)
    selected_segment = st.selectbox(
        "Segmento",
        ["Todos", *sorted(historical["segmento"].unique().tolist())],
    )
    if st.button("Limpiar conversación", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

st.title("🚢 Asistente de Inteligencia del Canal")
st.caption(
    "Consulta el histórico 2020–2025, predicciones 2026, países, clusters "
    "y desempeño de los modelos."
)

filtered_hist = historical
filtered_pred = predictions
if selected_segment != "Todos":
    filtered_hist = historical[historical["segmento"] == selected_segment]
    filtered_pred = predictions[predictions["segmento"] == selected_segment]

c1, c2, c3, c4 = st.columns(4)
c1.metric("Tránsitos históricos", f"{filtered_hist['transitos'].sum():,.0f}")
c2.metric(
    "Ingresos históricos",
    f"US${filtered_hist['ingresos'].sum() / 1_000_000:,.1f} M",
)
c3.metric("Tránsitos previstos 2026", f"{filtered_pred['pred_transitos'].sum():,.0f}")
c4.metric(
    "Ingresos previstos 2026",
    f"US${filtered_pred['pred_ingresos'].sum() / 1_000_000:,.1f} M",
)

chart_data = pd.concat(
    [
        filtered_hist[["fecha", "segmento", "ingresos"]].rename(
            columns={"ingresos": "valor"}
        ).assign(serie="Histórico"),
        filtered_pred[["fecha", "segmento", "pred_ingresos"]].rename(
            columns={"pred_ingresos": "valor"}
        ).assign(serie="Predicción"),
    ],
    ignore_index=True,
)
fig = px.line(
    chart_data,
    x="fecha",
    y="valor",
    color="serie",
    line_dash="segmento",
    labels={"fecha": "Fecha", "valor": "Ingresos (USD)", "serie": "Serie"},
    color_discrete_map={"Histórico": "#0B3C5D", "Predicción": "#F2A900"},
)
fig.update_layout(height=310, margin=dict(l=10, r=10, t=20, b=10))
st.plotly_chart(fig, use_container_width=True)

st.subheader("Conversación")
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

question = st.chat_input("Ej.: ¿Qué segmento tendrá mayores ingresos en 2026?")
if question:
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        with st.spinner("Analizando los datos..."):
            try:
                if api_key:
                    answer = ask_llm(
                        question,
                        st.session_state.messages[:-1],
                        compact_context(data),
                        api_key,
                        model,
                    )
                else:
                    answer = fallback_answer(question, data)
            except Exception as exc:
                answer = (
                    "No pude consultar el modelo en este momento. "
                    f"Detalle técnico: `{type(exc).__name__}`. "
                    "Verifica la API key, el modelo configurado y la conexión."
                )
            st.markdown(answer)
    st.session_state.messages.append({"role": "assistant", "content": answer})


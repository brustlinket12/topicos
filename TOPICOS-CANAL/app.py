# Análisis de Datos del Canal de Panamá

import os
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

import pandas as pd
import numpy as np
import requests
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from sklearn.linear_model import LinearRegression

DATA_DIR = Path(__file__).parent
BUQUES_CSV = DATA_DIR / "Trafico_Buques_Segmento_Mercado_Canal_Panama.csv"
PAISES_CSV = DATA_DIR / "Principales_Paises_Flujo_Carga_Canal_Panama.csv"
DEFAULT_OLLAMA_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434").rstrip("/")
DEFAULT_OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:1b")
OLLAMA_TIMEOUT = int(os.getenv("OLLAMA_TIMEOUT", "120"))

COUNTRY_ISO3 = {
    "Estados Unidos": "USA",
    "China": "CHN",
    "Japón": "JPN",
    "Chile": "CHL",
    "Corea del Sur": "KOR",
    "Perú": "PER",
    "México": "MEX",
    "Colombia": "COL",
    "Ecuador": "ECU",
    "Canadá": "CAN",
    "Panamá": "PAN",
    "Brasil": "BRA",
    "España": "ESP",
    "Guatemala": "GTM",
    "Holanda (Países Bajos)": "NLD",
}


@st.cache_data
def load_buques():
    df = pd.read_csv(BUQUES_CSV)
    df = df[df["Segmento de Mercado"] != "Total"].copy()
    df["% Diferencia Tránsitos"] = (
        df["% Diferencia Tránsitos"]
        .str.replace("%", "", regex=False)
        .str.strip()
        .astype(float)
    )
    df["Toneladas Largas de Carga 2024"] = df["Toneladas Largas de Carga 2024"].fillna(0)
    df["Toneladas Largas de Carga 2025"] = df["Toneladas Largas de Carga 2025"].fillna(0)
    df["Cambio"] = df["Tránsitos 2025"] - df["Tránsitos 2024"]
    return df


@st.cache_data
def load_paises():
    df = pd.read_csv(PAISES_CSV)
    df["Costa a Costa"] = df["Costa a Costa"].fillna(0)
    return df


@st.cache_resource
def train_model(buques):
    X = buques[["Tránsitos 2024"]].values
    y = buques["Tránsitos 2025"].values
    model = LinearRegression()
    model.fit(X, y)
    return model


@st.cache_data
def get_predictions(_model, buques):
    X_2026 = buques[["Tránsitos 2025"]].values
    preds = _model.predict(X_2026)
    return preds


def get_ollama_models(base_url):
    """Comprueba la conexión y devuelve los modelos instalados."""
    try:
        response = requests.get(f"{base_url.rstrip('/')}/api/tags", timeout=5)
        response.raise_for_status()
        models = response.json().get("models", [])
        return [item.get("name") or item.get("model") for item in models]
    except requests.RequestException:
        return []


def generate_with_ollama(base_url, model, prompt):
    """Envía una consulta no-streaming a la API local de Ollama."""
    response = requests.post(
        f"{base_url.rstrip('/')}/api/generate",
        json={
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.2},
        },
        timeout=OLLAMA_TIMEOUT,
    )
    response.raise_for_status()
    data = response.json()
    text = data.get("response", "").strip()
    if not text:
        raise ValueError("Ollama respondió sin contenido.")
    return text


st.set_page_config(page_title="Canal de Panamá - Dashboard", layout="wide")

st.title("Análisis de Datos del Canal de Panamá")

buques = load_buques()
paises = load_paises()
model = train_model(buques)
preds_2026 = get_predictions(model, buques)

total_2024 = int(buques["Tránsitos 2024"].sum())
total_2025 = int(buques["Tránsitos 2025"].sum())
variacion = (total_2025 - total_2024) / total_2024 * 100

crecimiento = buques.loc[buques["Cambio"].idxmax()]
caida = buques.loc[buques["Cambio"].idxmin()]
pais_top = paises.loc[paises["Total"].idxmax()]
pred_total_2026 = int(preds_2026.sum())

col1, col2, col3, col4, col5, col6, col7 = st.columns(7)
col1.metric("Tránsitos 2024", f"{total_2024:,}")
col2.metric("Tránsitos 2025", f"{total_2025:,}")
col3.metric("Variación %", f"{variacion:.2f}%")
col4.metric("Mayor crecimiento", crecimiento["Segmento de Mercado"], f"+{int(crecimiento['Cambio'])}")
col5.metric("Mayor caída", caida["Segmento de Mercado"], f"{int(caida['Cambio'])}")
col6.metric("Top país", pais_top["País"], f"{pais_top['Total']/1e6:.1f}M ton")
col7.metric("Predicción 2026", f"{pred_total_2026:,}")

st.divider()

col_chart1, col_chart2 = st.columns(2)

with col_chart1:
    st.subheader("Tránsitos 2024 vs 2025 por Segmento")
    fig = go.Figure()
    x = range(len(buques))
    fig.add_trace(go.Bar(x=list(x), y=buques["Tránsitos 2024"], name="2024", marker_color="steelblue"))
    fig.add_trace(go.Bar(x=list(x), y=buques["Tránsitos 2025"], name="2025", marker_color="seagreen"))
    fig.update_layout(
        xaxis_tickangle=45,
        xaxis_ticktext=buques["Segmento de Mercado"].tolist(),
        yaxis_title="Número de tránsitos",
        barmode="group",
        height=400,
    )
    st.plotly_chart(fig, use_container_width=True)

with col_chart2:
    st.subheader("% Diferencia Tránsitos por Segmento")
    colors = ["green" if c > 0 else "red" for c in buques["Cambio"]]
    fig2 = go.Figure()
    fig2.add_trace(go.Bar(
        x=buques["Segmento de Mercado"],
        y=buques["% Diferencia Tránsitos"],
        marker_color=colors,
    ))
    fig2.update_layout(
        xaxis_tickangle=45,
        yaxis_title="Variación %",
        height=400,
    )
    st.plotly_chart(fig2, use_container_width=True)

st.divider()

col_map, col_top = st.columns([2, 1])

with col_map:
    st.subheader("Volumen de Carga por País")
    paises_map = paises.copy()
    paises_map["ISO3"] = paises_map["País"].map(COUNTRY_ISO3)
    paises_map = paises_map.dropna(subset=["ISO3"])
    fig3 = go.Figure(go.Choropleth(
        locations=paises_map["ISO3"],
        z=paises_map["Total"],
        text=paises_map["País"],
        colorscale="Blues",
        colorbar_title="Toneladas",
    ))
    fig3.update_layout(height=400, margin=dict(l=0, r=0, t=0, b=0))
    st.plotly_chart(fig3, use_container_width=True)

with col_top:
    st.subheader("Top Países por Total")
    top10 = paises.nlargest(10, "Total")
    fig4 = go.Figure(go.Bar(
        y=top10["País"][::-1],
        x=top10["Total"][::-1] / 1e6,
        orientation="h",
        marker_color="steelblue",
    ))
    fig4.update_layout(xaxis_title="Millones de toneladas", height=400)
    st.plotly_chart(fig4, use_container_width=True)

st.divider()

st.subheader("Predicción 2026 por Segmento")
buques_pred = buques.copy()
buques_pred["Predicción 2026"] = preds_2026.round(0).astype(int)
fig5 = go.Figure()
x = range(len(buques_pred))
fig5.add_trace(go.Bar(x=list(x), y=buques_pred["Tránsitos 2024"], name="2024", marker_color="steelblue"))
fig5.add_trace(go.Bar(x=list(x), y=buques_pred["Tránsitos 2025"], name="2025", marker_color="seagreen"))
fig5.add_trace(go.Bar(x=list(x), y=buques_pred["Predicción 2026"], name="2026 (predicción)", marker_color="orange"))
fig5.update_layout(
    xaxis_tickangle=45,
    xaxis_ticktext=buques_pred["Segmento de Mercado"].tolist(),
    yaxis_title="Número de tránsitos",
    barmode="group",
    height=400,
)
st.plotly_chart(fig5, use_container_width=True)

st.divider()

st.subheader("Resumen Ejecutivo")

with st.sidebar:
    st.header("Configuración LLM")
    llm_mode = st.radio(
        "Modo de resumen",
        options=["Ollama local", "OpenRouter", "Automático (sin LLM)"],
        index=0,
        help="Selecciona el modo de generación del resumen ejecutivo"
    )

    api_key_input = None
    ollama_model = None
    ollama_base_url = None
    model_input = None

    if llm_mode == "OpenRouter":
        api_key_input = st.text_input(
            "OPENROUTER_API_KEY",
            type="password",
            value=os.getenv("OPENROUTER_API_KEY", ""),
        )
        model_input = st.text_input(
            "Modelo",
            value=os.getenv("OPENROUTER_MODEL", "nvidia/nemotron-3-ultra-550b-a55b:free"),
        )
    elif llm_mode == "Ollama local":
        ollama_base_url = st.text_input(
            "URL de Ollama",
            value=DEFAULT_OLLAMA_URL,
            help="Usa 127.0.0.1 cuando Streamlit y Ollama corren en la misma computadora.",
        )
        installed_models = get_ollama_models(ollama_base_url)

        if installed_models:
            default_index = (
                installed_models.index(DEFAULT_OLLAMA_MODEL)
                if DEFAULT_OLLAMA_MODEL in installed_models
                else 0
            )
            ollama_model = st.selectbox(
                "Modelo Ollama",
                options=installed_models,
                index=default_index,
            )
            st.success("Ollama conectado")
        else:
            ollama_model = st.text_input(
                "Modelo Ollama",
                value=DEFAULT_OLLAMA_MODEL,
            )
            st.warning(
                "No se detectó Ollama. Inícialo y descarga el modelo con "
                "`ollama pull llama3.2:1b`."
            )

    generate_btn = st.button("Generar resumen")

kpis_text = (
    f"Tránsitos 2024: {total_2024:,} | "
    f"Tránsitos 2025: {total_2025:,} | "
    f"Variación: {variacion:.2f}% | "
    f"Mayor crecimiento: {crecimiento['Segmento de Mercado']} (+{int(crecimiento['Cambio'])}) | "
    f"Mayor caída: {caida['Segmento de Mercado']} ({int(caida['Cambio'])}) | "
    f"Top país: {pais_top['País']} ({pais_top['Total']/1e6:.1f}M ton) | "
    f"Predicción 2026: {pred_total_2026:,} tránsitos"
)

auto_summary = (
    f"En 2025 el Canal de Panamá registró {total_2025:,} tránsitos, "
    f"un {variacion:.2f}% más que los {total_2024:,} de 2024. "
    f"El segmento de {crecimiento['Segmento de Mercado']} fue el de mayor crecimiento absoluto "
    f"({int(crecimiento['Cambio'])} barcos más). "
    f"Por volumen de carga, {pais_top['País']} lidera el ranking. "
    f"El modelo lineal predice {pred_total_2026:,} tránsitos para 2026. "
    f"Esta predicción es una estimación simplificada y no constituye una garantía."
)


def get_llm_summary(
    kpis_text,
    llm_mode,
    api_key=None,
    ollama_model=None,
    ollama_base_url=None,
    openrouter_model=None,
    user_question=None,
):
    if llm_mode == "Automático (sin LLM)":
        return auto_summary, "Resumen automático"

    if llm_mode == "OpenRouter":
        if not api_key:
            st.warning("Por favor ingresa tu OPENROUTER_API_KEY")
            return auto_summary, "Resumen automático"
        try:
            from openai import OpenAI
            client = OpenAI(api_key=api_key, base_url="https://openrouter.ai/api/v1")
            prompt = (
                f"Este es un proyecto académico de simulación. No es una empresa real ni contiene información sensible. "
                f"Resume en español en máximo 120 palabras el siguiente análisis del Canal de Panamá. "
                f" Incluye los KPIs clave y un aviso de que la predicción es un modelo lineal simple:\n\n"
                f"{kpis_text}"
            )
            response = client.chat.completions.create(
                model=openrouter_model or "nvidia/nemotron-3-ultra-550b-a55b:free",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=250,
            )
            return response.choices[0].message.content, "Generado con OpenRouter"
        except Exception as e:
            st.error(f"Error con OpenRouter: {e}")
            return auto_summary, "Resumen automático"

    if llm_mode == "Ollama local":
        question = (user_question or "").strip()
        task = (
            f"Responde esta pregunta: {question}"
            if question
            else "Genera un resumen ejecutivo de máximo 120 palabras."
        )
        prompt = (
            "Eres un analista de datos del Canal de Panamá. "
            "Responde en español, usa solamente los datos proporcionados y no inventes cifras. "
            "Si los datos no permiten responder, dilo claramente. "
            f"{task}\n\nDATOS:\n{kpis_text}"
        )
        try:
            model = ollama_model or "llama3.2:1b"
            summary = generate_with_ollama(
                ollama_base_url or DEFAULT_OLLAMA_URL,
                model,
                prompt,
            )
            return summary, f"Generado localmente con Ollama ({model})"
        except requests.ConnectionError:
            st.error(
                "No se pudo conectar con Ollama. Ejecuta `ollama serve` "
                "y verifica la URL configurada."
            )
            return auto_summary, "Resumen automático (Ollama sin conexión)"
        except requests.Timeout:
            st.error(
                f"Ollama superó el tiempo de espera de {OLLAMA_TIMEOUT} segundos. "
                "Prueba un modelo más pequeño."
            )
            return auto_summary, "Resumen automático (timeout de Ollama)"
        except requests.HTTPError as error:
            detail = error.response.text[:300] if error.response is not None else str(error)
            st.error(f"Ollama devolvió un error HTTP: {detail}")
            return auto_summary, "Resumen automático (error de Ollama)"
        except (ValueError, requests.RequestException) as error:
            st.error(f"No fue posible generar la respuesta con Ollama: {error}")
            return auto_summary, "Resumen automático"

    return auto_summary, "Resumen automático"


user_question = st.text_area(
    "Pregunta opcional para Ollama",
    placeholder="Ejemplo: ¿Qué segmento tuvo el cambio más importante y por qué?",
    help="Déjalo vacío para generar un resumen ejecutivo.",
)

if generate_btn:
    summary, caption = get_llm_summary(
        kpis_text,
        llm_mode,
        api_key=api_key_input if llm_mode == "OpenRouter" else None,
        ollama_model=ollama_model if llm_mode == "Ollama local" else None,
        ollama_base_url=ollama_base_url if llm_mode == "Ollama local" else None,
        openrouter_model=model_input if llm_mode == "OpenRouter" else None,
        user_question=user_question,
    )
    st.markdown(f"**Resumen ejecutivo**  \n{summary}")
    st.caption(caption)

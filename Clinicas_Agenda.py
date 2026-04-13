"""
MVP — Optimizador de Agenda y Facturación · Clínicas y Consultas Médicas
─────────────────────────────────────────────────────────────────────────
Problema resuelto : Baches de agenda donde los doctores no producen,
                    no-shows que destruyen facturación y mezcla de
                    especialidades con distinto margen.
Datos             : Generados en memoria (sin CRM real)
Objetivo          : Vista ejecutiva para el director/gerente de clínica

Run:
    streamlit run "Clinicas_Agenda/Clinicas_Agenda.py"
"""

import datetime
import random

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

random.seed(7)
np.random.seed(7)

# ──────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG
# ──────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Optimizador de Agenda — Clínica",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ──────────────────────────────────────────────────────────────────────────────
# CUSTOM CSS
# ──────────────────────────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
        .stApp { background-color: #F0F4FF; }

        div[data-testid="metric-container"] {
            background: #FFFFFF;
            border-radius: 12px;
            padding: 18px 22px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.07);
            border-left: 4px solid #2563EB;
        }
        div[data-testid="metric-container"] label {
            font-size: 0.78rem;
            color: #6B7280;
            font-weight: 600;
            letter-spacing: 0.05em;
            text-transform: uppercase;
        }
        div[data-testid="metric-container"] div[data-testid="stMetricValue"] {
            font-size: 1.9rem;
            font-weight: 700;
            color: #111827;
        }
        .section-header {
            font-size: 1.05rem;
            font-weight: 700;
            color: #1E3A8A;
            border-bottom: 2px solid #2563EB;
            padding-bottom: 5px;
            margin-bottom: 4px;
            margin-top: 8px;
        }
        div[data-testid="stInfo"] {
            background-color: #EFF6FF;
            border-left: 4px solid #2563EB;
            border-radius: 8px;
        }
        div[data-testid="stWarning"] {
            background-color: #FFFBEB;
            border-left: 4px solid #D97706;
            border-radius: 8px;
        }
        div[data-testid="stError"] {
            background-color: #FEF2F2;
            border-left: 4px solid #DC2626;
            border-radius: 8px;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# ──────────────────────────────────────────────────────────────────────────────
# DATOS MAESTROS
# ──────────────────────────────────────────────────────────────────────────────
ESPECIALIDADES = {
    "Medicina General":      {"tarifa": 55,  "duracion_min": 20, "margen_pct": 0.52},
    "Dermatología":          {"tarifa": 90,  "duracion_min": 30, "margen_pct": 0.61},
    "Estética / Láser":      {"tarifa": 220, "duracion_min": 45, "margen_pct": 0.72},
    "Fisioterapia":          {"tarifa": 50,  "duracion_min": 40, "margen_pct": 0.48},
    "Nutrición":             {"tarifa": 65,  "duracion_min": 30, "margen_pct": 0.58},
    "Odontología General":   {"tarifa": 80,  "duracion_min": 45, "margen_pct": 0.55},
    "Ortodoncia":            {"tarifa": 150, "duracion_min": 30, "margen_pct": 0.68},
    "Psicología":            {"tarifa": 75,  "duracion_min": 50, "margen_pct": 0.56},
}

DOCTORES = {
    "Dra. Martínez":  ["Medicina General", "Dermatología"],
    "Dr. Gómez":      ["Fisioterapia"],
    "Dra. Ruiz":      ["Estética / Láser", "Dermatología"],
    "Dr. Sánchez":    ["Odontología General", "Ortodoncia"],
    "Dra. López":     ["Nutrición", "Psicología"],
    "Dr. Fernández":  ["Medicina General", "Psicología"],
}

BOXES = ["Box 1", "Box 2", "Box 3", "Box 4", "Box 5"]

# Tasa de no-show por especialidad (realista)
TASA_NOSHOW = {
    "Medicina General":    0.14,
    "Dermatología":        0.10,
    "Estética / Láser":    0.06,
    "Fisioterapia":        0.18,
    "Nutrición":           0.20,
    "Odontología General": 0.12,
    "Ortodoncia":          0.08,
    "Psicología":          0.22,
}

# ──────────────────────────────────────────────────────────────────────────────
# GENERACIÓN DE CITAS (Enero–Febrero 2026)
# ──────────────────────────────────────────────────────────────────────────────
def generar_citas(n: int = 1_100) -> pd.DataFrame:
    especialidades = list(ESPECIALIDADES.keys())
    doctores_list  = list(DOCTORES.keys())
    fechas = pd.date_range("2026-01-02", "2026-02-28", freq="B")   # solo laborables

    rows = []
    for _ in range(n):
        esp    = random.choice(especialidades)
        info   = ESPECIALIDADES[esp]
        doctor = random.choice([d for d, esps in DOCTORES.items() if esp in esps])
        box    = random.choice(BOXES)
        fecha  = random.choice(fechas)
        hora   = random.randint(8, 19)
        no_show = random.random() < TASA_NOSHOW[esp]
        facturado = 0.0 if no_show else info["tarifa"] * random.uniform(0.90, 1.0)
        margen    = facturado * info["margen_pct"] if not no_show else 0.0

        rows.append({
            "fecha":        fecha,
            "dia_semana":   fecha.day_name(),
            "hora":         hora,
            "especialidad": esp,
            "doctor":       doctor,
            "box":          box,
            "duracion_min": info["duracion_min"],
            "no_show":      no_show,
            "facturado":    round(facturado, 2),
            "margen":       round(margen, 2),
            "tarifa_std":   info["tarifa"],
        })
    return pd.DataFrame(rows)

df = generar_citas(1_100)

# ── KPIs globales ─────────────────────────────────────────────────────────────
total_citas       = len(df)
total_noshow      = df["no_show"].sum()
tasa_noshow_pct   = round(total_noshow / total_citas * 100, 1)
facturacion_total = df["facturado"].sum()
margen_total      = df["margen"].sum()
perdida_noshow    = (df[df["no_show"]]["tarifa_std"]).sum()

# Ocupación: minutos producidos / minutos disponibles totales
# Disponible: 8h/día × días laborables × boxes
dias_laborables = df["fecha"].dt.date.nunique()
minutos_disponibles = dias_laborables * 8 * 60 * len(BOXES)
minutos_producidos  = df[~df["no_show"]]["duracion_min"].sum()
tasa_ocupacion_pct  = round(minutos_producidos / minutos_disponibles * 100, 1)

ticket_promedio = round(df[~df["no_show"]]["facturado"].mean(), 2)

# ── Agrupaciones ──────────────────────────────────────────────────────────────
# Por especialidad
esp_perf = (
    df.groupby("especialidad")
    .agg(
        Citas       =("facturado", "count"),
        Facturación =("facturado", "sum"),
        Margen      =("margen", "sum"),
        No_Shows    =("no_show", "sum"),
        Tarifa_std  =("tarifa_std", "first"),
        Dur_min     =("duracion_min", "first"),
    )
    .reset_index()
)
esp_perf["Tasa_NS_%"]    = (esp_perf["No_Shows"] / esp_perf["Citas"] * 100).round(1)
esp_perf["Margen_%"]     = (esp_perf["Margen"] / esp_perf["Facturación"].replace(0, np.nan) * 100).round(1)
esp_perf["Ticket_medio"] = (esp_perf["Facturación"] / (esp_perf["Citas"] - esp_perf["No_Shows"]).replace(0, np.nan)).round(2)
esp_perf = esp_perf.sort_values("Facturación", ascending=False)

# Por doctor
doc_perf = (
    df.groupby("doctor")
    .agg(
        Citas        =("facturado", "count"),
        Facturación  =("facturado", "sum"),
        Margen       =("margen", "sum"),
        No_Shows     =("no_show", "sum"),
        Minutos_prod =("duracion_min", lambda x: x[~df.loc[x.index, "no_show"]].sum()),
    )
    .reset_index()
)
doc_perf["Tasa_NS_%"]   = (doc_perf["No_Shows"] / doc_perf["Citas"] * 100).round(1)
doc_perf["Ocupación_%"] = (doc_perf["Minutos_prod"] / (dias_laborables * 8 * 60) * 100).round(1)
doc_perf = doc_perf.sort_values("Facturación", ascending=False)

# Ocupación por box por hora del día (heatmap)
box_hora = (
    df[~df["no_show"]]
    .groupby(["box", "hora"])
    .size()
    .reset_index(name="citas")
)
heatmap_pivot = box_hora.pivot(index="box", columns="hora", values="citas").fillna(0)

# Serie diaria
df_diario = (
    df.assign(dia=df["fecha"].dt.date)
    .groupby("dia")
    .agg(
        facturacion =("facturado", "sum"),
        no_shows    =("no_show", "sum"),
        citas       =("facturado", "count"),
    )
    .reset_index()
)
df_diario["ocupacion"] = (df_diario["citas"] / (len(BOXES) * 8 * 60 / df["duracion_min"].mean()) * 100).round(1)

# No-show por día de la semana
noshow_dow = (
    df.groupby("dia_semana")
    .agg(ns=("no_show", "sum"), total=("no_show", "count"))
    .reset_index()
)
noshow_dow["tasa_%"] = (noshow_dow["ns"] / noshow_dow["total"] * 100).round(1)
orden_dias = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
noshow_dow = noshow_dow[noshow_dow["dia_semana"].isin(orden_dias)]
noshow_dow["dia_es"] = noshow_dow["dia_semana"].map({
    "Monday": "Lunes", "Tuesday": "Martes", "Wednesday": "Miércoles",
    "Thursday": "Jueves", "Friday": "Viernes"
})
noshow_dow = noshow_dow.set_index("dia_semana").loc[orden_dias].reset_index()

# ──────────────────────────────────────────────────────────────────────────────
# SIDEBAR
# ──────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.image("https://img.icons8.com/color/96/hospital-3.png", width=60)
    st.title("Agenda & Billing")
    st.caption("Dashboard de Clínica — Vista Gerencial")
    st.divider()

    st.markdown("**Periodo del informe**")
    _default_start = datetime.date(2026, 1, 1)
    _default_end   = datetime.date(2026, 2, 28)
    date_range = st.date_input(
        "Rango de fechas",
        value=(_default_start, _default_end),
        min_value=datetime.date(2025, 1, 1),
        max_value=datetime.date.today(),
        format="DD/MM/YYYY",
    )
    _meses_es = {
        1:"Enero", 2:"Febrero", 3:"Marzo", 4:"Abril",
        5:"Mayo",  6:"Junio",   7:"Julio", 8:"Agosto",
        9:"Septiembre", 10:"Octubre", 11:"Noviembre", 12:"Diciembre",
    }
    if isinstance(date_range, (list, tuple)) and len(date_range) == 2:
        periodo_label = (
            f"{_meses_es[date_range[0].month]} {date_range[0].year} "
            f"— {_meses_es[date_range[1].month]} {date_range[1].year}"
        )
    else:
        periodo_label = "Enero 2026 — Febrero 2026"

    st.divider()

    esp_sel = st.multiselect(
        "Especialidad",
        options=sorted(df["especialidad"].unique()),
        default=sorted(df["especialidad"].unique()),
    )
    doc_sel = st.multiselect(
        "Doctor / Terapeuta",
        options=sorted(df["doctor"].unique()),
        default=sorted(df["doctor"].unique()),
    )

    st.divider()
    umbral_ocup = st.slider(
        "Umbral alerta ocupación (%)",
        min_value=50, max_value=90, value=70, step=5,
        help="Se dispara alerta cuando la tasa de ocupación baja de este valor.",
    )

    st.divider()
    st.markdown("**Clínica simulada**")
    st.markdown("🏥 **Clínica Salude Premium**")
    st.caption(f"Periodo: **{periodo_label}**")
    st.caption(f"Boxes activos: **{len(BOXES)}** · Doctores: **{len(DOCTORES)}**")

# Filtrado
df_f = df[df["especialidad"].isin(esp_sel) & df["doctor"].isin(doc_sel)]
esp_perf_f = esp_perf[esp_perf["especialidad"].isin(esp_sel)]
doc_perf_f = doc_perf[doc_perf["doctor"].isin(doc_sel)]

# ──────────────────────────────────────────────────────────────────────────────
# HEADER
# ──────────────────────────────────────────────────────────────────────────────
st.markdown(
    "<h1 style='color:#1E3A8A; margin-bottom:2px;'>🏥 Optimizador de Agenda y Facturación</h1>",
    unsafe_allow_html=True,
)
st.markdown(
    f"<p style='color:#6B7280; font-size:0.95rem; margin-top:0;'>"
    f"Control de <b>Ocupación · No-Shows · Ticket medio · Rentabilidad por Especialidad</b>  —  {periodo_label}</p>",
    unsafe_allow_html=True,
)
st.divider()

# ──────────────────────────────────────────────────────────────────────────────
# SECCIÓN 1 — KPIs
# ──────────────────────────────────────────────────────────────────────────────
st.markdown("<div class='section-header'>📊 KPIs de Gestión Clínica</div>", unsafe_allow_html=True)

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric(
    "Tasa de Ocupación",
    f"{tasa_ocupacion_pct} %",
    delta=f"{'✅ OK' if tasa_ocupacion_pct >= umbral_ocup else '⚠️ Baja'}",
    delta_color="normal" if tasa_ocupacion_pct >= umbral_ocup else "inverse",
    help="Minutos de consulta producidos / minutos disponibles totales (boxes × horas × días).",
)
k2.metric(
    "Tasa de No-Show",
    f"{tasa_noshow_pct} %",
    delta=f"−€ {perdida_noshow:,.0f} perdidos",
    delta_color="inverse",
    help="Pacientes que no se presentaron a su cita. Cada % equivale a facturación directa perdida.",
)
k3.metric(
    "Facturación Total",
    f"€ {facturacion_total:,.0f}",
    delta="+9.3% vs periodo anterior",
)
k4.metric(
    "Margen Neto Clínica",
    f"€ {margen_total:,.0f}",
    delta=f"{round(margen_total/facturacion_total*100,1)} % s/facturación",
)
k5.metric(
    "Ticket Medio (atendido)",
    f"€ {ticket_promedio}",
    delta="por consulta efectiva",
)

# Alerta ocupación
if tasa_ocupacion_pct < umbral_ocup:
    st.error(
        f"🚨 **Alerta: Ocupación del {tasa_ocupacion_pct}%** — Por debajo del umbral configurado ({umbral_ocup}%). "
        f"La clínica pierde **€ {round((umbral_ocup - tasa_ocupacion_pct) / 100 * minutos_disponibles / 60 * ticket_promedio):,.0f}** "
        f"en potencial no materializado."
    )

st.markdown("<br>", unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────────────────────
# SECCIÓN 2 — OCUPACIÓN Y NO-SHOWS
# ──────────────────────────────────────────────────────────────────────────────
st.markdown("<div class='section-header'>⏱️ Ocupación por Box y Perfil de No-Shows</div>", unsafe_allow_html=True)

col_heat, col_dow = st.columns([3, 2])

with col_heat:
    st.caption("**Mapa de calor de uso de boxes por hora del día** — zonas frías = tiempo muerto")
    fig_heat = go.Figure(go.Heatmap(
        z=heatmap_pivot.values,
        x=[f"{h:02d}:00" for h in heatmap_pivot.columns],
        y=heatmap_pivot.index.tolist(),
        colorscale=[
            [0.0,  "#EFF6FF"],
            [0.35, "#93C5FD"],
            [0.70, "#2563EB"],
            [1.0,  "#1E3A8A"],
        ],
        showscale=True,
        text=heatmap_pivot.values.astype(int),
        texttemplate="%{text}",
        hovertemplate="Box: %{y}<br>Hora: %{x}<br>Citas: %{z}<extra></extra>",
    ))
    fig_heat.update_layout(
        height=280,
        margin=dict(t=10, b=20, l=10, r=10),
        plot_bgcolor="white",
        paper_bgcolor="white",
        font=dict(family="Inter, sans-serif", size=12),
        xaxis=dict(title="Hora del día"),
        yaxis=dict(title=""),
    )
    st.plotly_chart(fig_heat, use_container_width=True)

with col_dow:
    st.caption("**No-Shows por día de la semana** — ¿cuándo llaman menos?")
    colors_dow = ["#EF4444" if v > 18 else "#F59E0B" if v > 12 else "#2563EB"
                  for v in noshow_dow["tasa_%"]]
    fig_dow = go.Figure(go.Bar(
        x=noshow_dow["dia_es"],
        y=noshow_dow["tasa_%"],
        marker_color=colors_dow,
        text=[f"{v}%" for v in noshow_dow["tasa_%"]],
        textposition="outside",
    ))
    fig_dow.add_hline(y=15, line_dash="dot", line_color="#EF4444",
                      annotation_text="Umbral crítico 15%")
    fig_dow.update_layout(
        height=280,
        margin=dict(t=10, b=20, l=10, r=10),
        plot_bgcolor="white",
        paper_bgcolor="white",
        yaxis=dict(title="% No-Show", gridcolor="#F3F4F6", ticksuffix="%"),
        font=dict(family="Inter, sans-serif", size=12),
        showlegend=False,
    )
    st.plotly_chart(fig_dow, use_container_width=True)

# ──────────────────────────────────────────────────────────────────────────────
# SECCIÓN 3 — TICKET PROMEDIO Y MARGEN POR ESPECIALIDAD
# ──────────────────────────────────────────────────────────────────────────────
st.markdown("<div class='section-header'>💶 Ticket Promedio y Margen por Especialidad</div>", unsafe_allow_html=True)
st.caption("La especialidad que más pacientes tiene **no es siempre** la que más margen deja.")

col_tick, col_marg = st.columns(2)

with col_tick:
    esp_sorted_ticket = esp_perf_f.sort_values("Ticket_medio", ascending=True)
    fig_ticket = go.Figure(go.Bar(
        x=esp_sorted_ticket["Ticket_medio"],
        y=esp_sorted_ticket["especialidad"],
        orientation="h",
        marker_color="#2563EB",
        text=[f"€{v:.0f}" for v in esp_sorted_ticket["Ticket_medio"]],
        textposition="outside",
    ))
    fig_ticket.update_layout(
        title=dict(text="Ticket Medio por Especialidad (€)", font=dict(size=13)),
        height=350,
        margin=dict(t=40, b=10, l=10, r=50),
        plot_bgcolor="white",
        paper_bgcolor="white",
        xaxis=dict(title="€", gridcolor="#F3F4F6"),
        font=dict(family="Inter, sans-serif", size=12),
    )
    st.plotly_chart(fig_ticket, use_container_width=True)

with col_marg:
    esp_sorted_marg = esp_perf_f.sort_values("Margen_%", ascending=True)
    col_marg_colors = [
        "#EF4444" if v < 50 else "#F59E0B" if v < 60 else "#2563EB"
        for v in esp_sorted_marg["Margen_%"]
    ]
    fig_marg = go.Figure(go.Bar(
        x=esp_sorted_marg["Margen_%"],
        y=esp_sorted_marg["especialidad"],
        orientation="h",
        marker_color=col_marg_colors,
        text=[f"{v}%" for v in esp_sorted_marg["Margen_%"]],
        textposition="outside",
    ))
    fig_marg.add_vline(x=60, line_dash="dot", line_color="#2563EB",
                       annotation_text="Objetivo 60%", annotation_position="top right")
    fig_marg.update_layout(
        title=dict(text="Margen Neto % por Especialidad", font=dict(size=13)),
        height=350,
        margin=dict(t=40, b=10, l=10, r=50),
        plot_bgcolor="white",
        paper_bgcolor="white",
        xaxis=dict(title="% Margen", gridcolor="#F3F4F6", ticksuffix="%"),
        font=dict(family="Inter, sans-serif", size=12),
    )
    st.plotly_chart(fig_marg, use_container_width=True)

# Donut de distribución de facturación
fig_donut = px.pie(
    esp_perf_f,
    names="especialidad",
    values="Facturación",
    hole=0.55,
    title="Distribución de Facturación por Especialidad",
    color_discrete_sequence=px.colors.sequential.Blues_r,
)
fig_donut.update_traces(textinfo="percent+label", textfont_size=12)
fig_donut.update_layout(
    height=280,
    margin=dict(t=40, b=10),
    paper_bgcolor="white",
    font=dict(family="Inter, sans-serif", size=12),
    legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
)
st.plotly_chart(fig_donut, use_container_width=True)

# ──────────────────────────────────────────────────────────────────────────────
# SECCIÓN 4 — RENDIMIENTO POR DOCTOR
# ──────────────────────────────────────────────────────────────────────────────
st.markdown("<div class='section-header'>👨‍⚕️ Rendimiento por Doctor</div>", unsafe_allow_html=True)
st.caption("Comparativa de facturación, ocupación y tasa de no-show individual.")

col_doc_bar, col_doc_ocup = st.columns(2)

with col_doc_bar:
    fig_doc = go.Figure()
    fig_doc.add_trace(go.Bar(
        name="Facturación €",
        x=doc_perf_f["doctor"],
        y=doc_perf_f["Facturación"],
        marker_color="#2563EB",
        text=[f"€{v:,.0f}" for v in doc_perf_f["Facturación"]],
        textposition="outside",
    ))
    fig_doc.add_trace(go.Bar(
        name="Margen €",
        x=doc_perf_f["doctor"],
        y=doc_perf_f["Margen"],
        marker_color="#93C5FD",
        text=[f"€{v:,.0f}" for v in doc_perf_f["Margen"]],
        textposition="outside",
    ))
    fig_doc.update_layout(
        barmode="group",
        title=dict(text="Facturación y Margen por Doctor", font=dict(size=13)),
        height=340,
        margin=dict(t=40, b=20, l=10, r=10),
        plot_bgcolor="white",
        paper_bgcolor="white",
        yaxis=dict(title="€", gridcolor="#F3F4F6"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        font=dict(family="Inter, sans-serif", size=11),
        xaxis=dict(tickangle=-15),
    )
    st.plotly_chart(fig_doc, use_container_width=True)

with col_doc_ocup:
    fig_ocup = go.Figure()
    colores_ocup = [
        "#EF4444" if v < umbral_ocup else "#F59E0B" if v < umbral_ocup + 10 else "#2563EB"
        for v in doc_perf_f["Ocupación_%"]
    ]
    fig_ocup.add_trace(go.Bar(
        name="Ocupación %",
        x=doc_perf_f["doctor"],
        y=doc_perf_f["Ocupación_%"],
        marker_color=colores_ocup,
        text=[f"{v}%" for v in doc_perf_f["Ocupación_%"]],
        textposition="outside",
    ))
    fig_ocup.add_hline(
        y=umbral_ocup, line_dash="dot", line_color="#EF4444",
        annotation_text=f"Umbral {umbral_ocup}%",
    )
    fig_ocup.update_layout(
        title=dict(text="Tasa de Ocupación por Doctor (%)", font=dict(size=13)),
        height=340,
        margin=dict(t=40, b=20, l=10, r=10),
        plot_bgcolor="white",
        paper_bgcolor="white",
        yaxis=dict(title="% Ocupación", gridcolor="#F3F4F6", ticksuffix="%", range=[0, 100]),
        font=dict(family="Inter, sans-serif", size=11),
        showlegend=False,
        xaxis=dict(tickangle=-15),
    )
    st.plotly_chart(fig_ocup, use_container_width=True)

# ──────────────────────────────────────────────────────────────────────────────
# SECCIÓN 5 — TABLA DETALLE ESPECIALIDADES
# ──────────────────────────────────────────────────────────────────────────────
st.markdown("<div class='section-header'>📋 Detalle de Rentabilidad por Especialidad</div>", unsafe_allow_html=True)

def color_ns(val):
    if val >= 18:
        return "background-color:#FEE2E2;color:#991B1B;font-weight:600"
    elif val >= 12:
        return "background-color:#FEF9C3;color:#92400E;font-weight:600"
    return "background-color:#DBEAFE;color:#1E3A8A;font-weight:600"

def color_margen_esp(val):
    if val < 50:
        return "background-color:#FEE2E2;color:#991B1B;font-weight:600"
    elif val < 60:
        return "background-color:#FEF9C3;color:#92400E;font-weight:600"
    return "background-color:#DBEAFE;color:#1E3A8A;font-weight:600"

cols_esp = ["especialidad", "Citas", "No_Shows", "Tasa_NS_%", "Facturación", "Margen", "Margen_%", "Ticket_medio"]
df_esp_tabla = esp_perf_f[cols_esp].rename(columns={
    "especialidad": "Especialidad",
    "No_Shows":     "No-Shows",
    "Tasa_NS_%":    "NS %",
    "Facturación":  "Facturación €",
    "Margen":       "Margen €",
    "Margen_%":     "Margen %",
    "Ticket_medio": "Ticket €",
})

styled_esp = (
    df_esp_tabla.style
    .format({
        "Facturación €": "€ {:,.0f}",
        "Margen €":      "€ {:,.0f}",
        "Ticket €":      "€ {:,.2f}",
        "NS %":          "{:.1f}%",
        "Margen %":      "{:.1f}%",
        "Citas":         "{:,}",
        "No-Shows":      "{:,}",
    })
    .applymap(color_ns,         subset=["NS %"])
    .applymap(color_margen_esp, subset=["Margen %"])
    .set_properties(**{"font-size": "0.86rem"})
    .set_table_styles([
        {"selector": "thead th", "props": [
            ("background-color", "#1E3A8A"),
            ("color", "white"),
            ("font-weight", "600"),
            ("font-size", "0.80rem"),
            ("padding", "9px 12px"),
        ]},
        {"selector": "tbody tr:nth-child(even)", "props": [
            ("background-color", "#EFF6FF"),
        ]},
        {"selector": "tbody td", "props": [("padding", "7px 12px")]},
    ])
)
st.dataframe(styled_esp, use_container_width=True, height=320)

# ──────────────────────────────────────────────────────────────────────────────
# SECCIÓN 6 — EVOLUCIÓN DIARIA
# ──────────────────────────────────────────────────────────────────────────────
st.markdown("<div class='section-header'>📅 Evolución Diaria — Facturación y No-Shows</div>", unsafe_allow_html=True)

fig_daily = go.Figure()
fig_daily.add_trace(go.Scatter(
    x=df_diario["dia"], y=df_diario["facturacion"],
    mode="lines", name="Facturación €",
    line=dict(color="#2563EB", width=2.5),
    fill="tozeroy", fillcolor="rgba(37,99,235,0.10)",
))
fig_daily.add_trace(go.Bar(
    x=df_diario["dia"], y=df_diario["no_shows"],
    name="No-Shows",
    marker_color="#EF4444",
    opacity=0.65,
    yaxis="y2",
))
fig_daily.add_hline(
    y=df_diario["facturacion"].mean(),
    line_dash="dot", line_color="#6B7280",
    annotation_text="Media diaria",
    annotation_position="top left",
)
fig_daily.update_layout(
    height=320,
    margin=dict(t=20, b=20, l=10, r=60),
    plot_bgcolor="white",
    paper_bgcolor="white",
    yaxis =dict(title="€ Facturación", gridcolor="#F3F4F6"),
    yaxis2=dict(title="Nº No-Shows", overlaying="y", side="right", showgrid=False),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    font=dict(family="Inter, sans-serif", size=12),
    hovermode="x unified",
)
st.plotly_chart(fig_daily, use_container_width=True)

# ──────────────────────────────────────────────────────────────────────────────
# SECCIÓN 7 — NOTA DE INGENIERÍA DE DATOS
# ──────────────────────────────────────────────────────────────────────────────
st.markdown("<div class='section-header'>⚙️ Nota Técnica — Integración CRM + Alertas Automáticas</div>", unsafe_allow_html=True)

st.info(
    f"""
    **¿Cómo se construye esta integración en producción?**

    La mayoría de clínicas usan software de gestión de citas como **Clinic Cloud, Dentix, Gesden o Jane App**.
    Estos sistemas exponen sus datos vía API REST o exportaciones SQL. El Data Engineer conecta esas fuentes
    para crear un pipeline de alertas en tiempo real:

    ---

    **📥 Fuente 1 — CRM / Software de citas (API REST o ODBC)**
    Extrae en tiempo real: citas programadas, confirmaciones, cancelaciones, llegadas tardías y no-shows.
    Se normaliza en la capa Bronze con campos estándar: `paciente_id`, `doctor_id`, `box`, `especialidad`, `estado`.

    **📥 Fuente 2 — Sistema de facturación (CSV / webhook)**
    Importa los actos facturados por sesión: tarifa aplicada, descuentos, seguro médico vs. particular.
    El join con las citas permite calcular el **margen real por consulta** (descuentando suministros y overhead de box).

    **📥 Fuente 3 — Google Calendar / Outlook Calendar**
    Sincronización bidireccional: cada cita del CRM se cruza con la disponibilidad del doctor.
    Permite detectar automáticamente **huecos de más de 30 min** en la agenda como tiempo muerto.

    ---

    **🔔 Sistema de alertas (umbral configurado: {umbral_ocup}% ocupación)**

    El DAG de Airflow evalúa cada hora la ocupación actual del día:
    ```python
    # Alerta automática vía Slack/WhatsApp si ocupación < umbral
    if ocupacion_actual < {umbral_ocup}:
        enviar_alerta(
            canal="#gerencia-clinica",
            mensaje=f"⚠️ Ocupación al {{ocupacion_actual}}% — quedan {{huecos}} huecos libres hoy."
        )
    ```

    **🔄 Pipeline (ejecución cada hora)**
    1. `extract_crm_appointments()` → citas del día en curso
    2. `extract_billing()` → actos facturados hasta ahora
    3. `transform_silver()` → join CRM + facturación + disponibilidad
    4. `compute_kpis()` → ocupación, no-show, ticket medio por doctor/box
    5. `alert_if_below_threshold()` → Slack + email si ocupación < umbral

    **Resultado:** la clínica recibe una alerta a las 9:00, 12:00 y 15:00 si hay huecos que rellenar,
    con una lista de pacientes en lista de espera para llamar proactivamente.

    **Tecnologías:** Python · Apache Airflow · dbt · PostgreSQL · Slack API · Streamlit Cloud
    """
)

# ──────────────────────────────────────────────────────────────────────────────
# FOOTER
# ──────────────────────────────────────────────────────────────────────────────
st.divider()
st.markdown(
    "<p style='text-align:center; color:#9CA3AF; font-size:0.8rem;'>"
    "MVP — Optimizador de Agenda y Facturación · Clínicas · Datos simulados · Streamlit + Plotly"
    "</p>",
    unsafe_allow_html=True,
)

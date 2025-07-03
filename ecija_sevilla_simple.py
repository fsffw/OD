import streamlit as st
import pandas as pd
from pyspainmobility import Mobility
import matplotlib.pyplot as plt
import folium
from shapely.geometry import LineString

st.set_page_config(page_title="Écija-Sevilla Mayo 2024", layout="wide")
st.title("🚍 Viajes Écija ↔ Sevilla – Mayo 2024")

# Parámetros fijos
ORIGIN = 41038  # Écija
DEST   = 41091  # Sevilla
START_DATE = "2024-05-01"
END_DATE   = "2024-05-31"

@st.cache_data
def load_data():
    # Descargar matriz OD completa de MITMA
    mob = Mobility(
        version=2,
        zones="municipalities",
        start_date=START_DATE,
        end_date=END_DATE,
        output_directory="data/raw"
    )
    od = mob.get_od_data(include_mode=True)
    # Filtrar viajes carretera entre Écija y Sevilla
    df = od[
        (od.ppal_mode == "C") & (
            ((od.origin == ORIGIN) & (od.destination == DEST)) |
            ((od.origin == DEST) & (od.destination == ORIGIN))
        )
    ]
    return df

# Carga datos
df = load_data()
total = int(df.travellers.sum())
st.metric("Total viajes mayo 2024", f"{total:,}")

# Serie diaria
st.subheader("Serie diaria de viajeros")
daily = df.groupby("date")["travellers"].sum().reset_index()
daily = daily.set_index("date")
st.line_chart(daily)

# Mapa de flujo simple
st.subheader("Mapa de flujo")
# Coordenadas aproximadas
coords = {
    ORIGIN: (37.566667, -5.066667),
    DEST:   (37.389092, -5.984459)
}
m = folium.Map(location=[37.5, -5.0], zoom_start=8)
max_trav = df.travellers.max() if not df.empty else 1
for _, row in df.iterrows():
    o, d, trav = row.origin, row.destination, row.travellers
    line = LineString([coords[o], coords[d]])
    weight = 1 + (trav / max_trav) * 5
    folium.GeoJson(
        line,
        style_function=lambda feat, w=weight: {"color": "blue", "weight": w}
    ).add_to(m)
st.components.v1.html(m._repr_html_(), height=400)

st.markdown("Datos: MITMA OpenData Movilidad (Municipalities v2)")

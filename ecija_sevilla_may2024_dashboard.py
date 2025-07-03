import streamlit as st
from pyspainmobility import Zones, Mobility
import pandas as pd, matplotlib.pyplot as plt
import folium
from shapely.geometry import LineString
from streamlit_folium import st_folium

st.set_page_config(page_title="Écija-Sevilla Mayo 2024", layout="wide")
st.title("🚍 Viajes Écija ↔ Sevilla – Mayo 2024")

# Parámetros fijos
ORIGIN = 41038  # Écija
DEST = 41091    # Sevilla
START_DATE = "2024-05-01"
END_DATE = "2024-05-31"

@st.cache_data
def load_data():
    # Zonas Andalucía
    zones = Zones(zones="municipalities", version=2, output_directory="data/zonas")
    gdf = zones.get_zone_geodataframe()
    # Descargar OD
    mob = Mobility(version=2, zones="municipalities", start_date=START_DATE, end_date=END_DATE, output_directory="data/raw")
    od = mob.get_od_data(include_mode=True)
    # Filtrar carretera y municipios específicos
    df = od[(od.ppal_mode=="C") & (
            ((od.origin==ORIGIN) & (od.destination==DEST)) |
            ((od.origin==DEST)  & (od.destination==ORIGIN))
        )]
    return df

df = load_data()
total = int(df.travellers.sum())
st.metric("Total viajes mayo 2024", f"{total:,}")

st.subheader("Serie diaria de viajeros")
daily = df.groupby("date")["travellers"].sum().reset_index()
daily = daily.set_index("date")
st.line_chart(daily)

st.subheader("Mapa de flujo")
# Centroides de municipios
zones = Zones(zones="municipalities", version=2, output_directory="data/zonas")
gdf = zones.get_zone_geodataframe()
gdf = gdf[gdf.ccaa_name=="Andalucía"][["zone_id","geometry"]]
gdf["geometry"] = gdf.geometry.centroid
import geopandas as gpd
centroids = gpd.GeoDataFrame(gdf, crs="EPSG:4326")

m = folium.Map([37.6, -4.7], zoom_start=7)
max_travellers = df.travellers.max()
for _, row in df.iterrows():
    o = row.origin; d = row.destination; trav = row.travellers
    o_geom = centroids.loc[centroids.zone_id==o, "geometry"].values[0]
    d_geom = centroids.loc[centroids.zone_id==d, "geometry"].values[0]
    line = LineString([o_geom, d_geom])
    weight = 1 + (trav / max_travellers) * 5
    folium.GeoJson(
        line,
        style_function=lambda feat, w=weight: {"color": "blue", "weight": w}
    ).add_to(m)
st_folium(m, width="100%", height=500)

st.markdown("Datos: MITMA OpenData Movilidad (Municipalities v2)")

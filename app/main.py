import streamlit as st
import pandas as pd
import geopandas as gpd
import folium
from streamlit_folium import st_folium
from pathlib import Path
import os
import sys
from dotenv import load_dotenv
import subprocess

# Cargar variables de entorno
load_dotenv()
COMUNA_NAME = os.getenv("COMUNA_NAME", "Peñaflor")
DATA_DIR = Path("data/raw")

# Sidebar
with st.sidebar:
    st.image("https://via.placeholder.com/300x100?text=Logo+USACH", width=300)
    st.markdown("---")
    page = st.selectbox("Seleccione una sección:", ["🏠 Inicio", "📊 Datos", "🗺️ Análisis Espacial"])
    st.markdown("---")
    st.info("**Laboratorio Integrador**\n\nGeoinformática 2025\n\nUSACH")

# Botón para descargar datos manualmente
st.sidebar.markdown("### 📥 Descarga de Datos")
if st.sidebar.button("📥 Descargar Datos Geoespaciales"):
    with st.spinner("Descargando datos para la comuna seleccionada..."):
        subprocess.run([sys.executable, "scripts/download_data.py"])
    st.success("✅ Datos descargados correctamente. Recarga la página para ver los cambios.")

# Botón para procesar datos
st.sidebar.markdown("### 🛠️ Procesamiento de Datos")
if st.sidebar.button("⚙️ Procesar Datos en PostGIS"):
    with st.spinner("Procesando datos y cargando en PostGIS..."):
        subprocess.run([sys.executable, "scripts/process_data.py"])
    st.success("✅ Datos procesados y cargados en PostGIS correctamente.")

# Cargar datos
boundary_path = DATA_DIR / "comuna_boundaries.geojson"
buildings_path = DATA_DIR / "osm_buildings.geojson"
amenities_path = DATA_DIR / "osm_amenities.geojson"
metadata_path = DATA_DIR / "metadata.txt"

comuna_gdf = gpd.read_file(boundary_path) if boundary_path.exists() else None
buildings_gdf = gpd.read_file(buildings_path) if buildings_path.exists() else None
amenities_gdf = gpd.read_file(amenities_path) if amenities_path.exists() else None

# Fallback: usar polígono aproximado desde edificios OSM si no hay límites
if comuna_gdf is None and buildings_gdf is not None:
    comuna_gdf = gpd.GeoDataFrame(geometry=[buildings_gdf.unary_union], crs=buildings_gdf.crs)
    st.warning("⚠️ Usando polígono aproximado desde edificios OSM como límite comunal.")

# Coordenadas del centro
centroid = comuna_gdf.geometry.centroid.iloc[0] if comuna_gdf is not None else None

# Configuración de la página
st.set_page_config(page_title="Análisis Territorial - Laboratorio Integrador", page_icon="🗺️", layout="wide")

# Título principal
st.title("🗺️ Sistema de Análisis Territorial")
st.markdown(f"### Comuna: {COMUNA_NAME}")

# Página: Inicio
if page == "🏠 Inicio":
    st.subheader("📍 Ubicación de la Comuna")
    if comuna_gdf is not None and centroid is not None:
        m = folium.Map(location=[centroid.y, centroid.x], zoom_start=12)
        folium.GeoJson(comuna_gdf, name="Límite Comunal").add_to(m)
        folium.LayerControl().add_to(m)
        st_folium(m, height=500, width=None)
    else:
        st.warning("No se pudo cargar el límite comunal.")

# Página: Datos
elif page == "📊 Datos":
    st.header("📊 Exploración de Datos")
    tab1, tab2, tab3 = st.tabs(["📋 Resumen", "📈 Estadísticas", "🗂️ Metadatos"])

    with tab1:
        st.subheader("Fuentes de Datos Integradas")
        data_sources = pd.DataFrame({
            'Fuente': ['OpenStreetMap', 'IDE Chile'],
            'Tipo': ['Vectorial', 'Vectorial'],
            'Estado': [
                '✅ Cargado' if buildings_gdf is not None else '⏳ Pendiente',
                '✅ Cargado' if comuna_gdf is not None else '⏳ Pendiente'
            ]
        })
        st.dataframe(data_sources)

    with tab2:
        st.subheader("Estadísticas de Edificios y Amenidades")
        if buildings_gdf is not None:
            st.write("🏢 Tipos de edificios más comunes:")
            st.dataframe(buildings_gdf['building'].value_counts().head(10))
        if amenities_gdf is not None:
            st.write("🏥 Tipos de amenidades más comunes:")
            st.dataframe(amenities_gdf['amenity'].value_counts().head(10))

    with tab3:
        st.subheader("Metadatos del Proyecto")
        if metadata_path.exists():
            with open(metadata_path, 'r') as f:
                st.text(f.read())
        else:
            st.warning("No se encontró el archivo de metadatos.")

# Página: Análisis Espacial
elif page == "🗺️ Análisis Espacial":
    st.header("🗺️ Análisis Espacial")
    st.info("Aquí se mostrará el análisis de autocorrelación espacial y clustering.")

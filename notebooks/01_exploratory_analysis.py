import os
from pathlib import Path
import nbformat as nbf

# Definir carpeta notebooks
notebooks = "notebooks"
notebooks_dir = Path(notebooks)
notebooks_dir.mkdir(parents=True, exist_ok=True)

# Crear notebook
nb = nbf.v4.new_notebook()

# Celdas de código para el análisis espacial exploratorio
cells = [
    nbf.v4.new_markdown_cell("""# 🧭 Análisis de Autocorrelación Espacial

Este notebook contiene el análisis espacial exploratorio (ESDA) para la comuna de Peñaflor, incluyendo:

- Estadísticas descriptivas espaciales
- Mapas temáticos
- Moran's I global y local
- Hot spots y clusters (LISA)
- Análisis de componentes principales espaciales (PCA)
"""),

    nbf.v4.new_code_cell("""import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import pysal
from pysal.lib import weights
from pysal.explore import esda
import splot.esda as splot

# Cargar datos de edificios como ejemplo
gdf = gpd.read_file("../data/raw/osm_buildings.geojson")

# Crear variable sintética área de cada edificio
gdf = gdf.to_crs(epsg=32719)
gdf['area'] = gdf.geometry.area

# Filtrar geometrías válidas
gdf = gdf[gdf.geometry.notnull()].copy()

# Crear matriz de pesos espaciales (Queen contiguity)
w = weights.Queen.from_dataframe(gdf)
w.transform = 'r'

# Moran's I Global
mi = esda.Moran(gdf['area'], w)
print(f"Moran's I: {mi.I:.4f}")
print(f"P-value: {mi.p_norm:.4f}")

# LISA - Moran Local
lisa = esda.Moran_Local(gdf['area'], w)

# Visualización
fig, axes = plt.subplots(1, 2, figsize=(15, 6))
splot.moran_scatterplot(mi, ax=axes[0])
splot.lisa_cluster(lisa, gdf, ax=axes[1])
plt.show()
"""),

    nbf.v4.new_code_cell("""# Preparación para PCA espacial (multivariado)
# Simulación de variables adicionales

from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA

# Crear variables sintéticas
gdf['compactness'] = gdf.geometry.length / (2 * np.sqrt(np.pi * gdf['area']))
gdf['density'] = gdf['area'] / gdf['area'].max()

# Normalizar variables
X = gdf[['area', 'compactness', 'density']].fillna(0)
X_scaled = StandardScaler().fit_transform(X)

# PCA espacial
pca = PCA(n_components=2)
components = pca.fit_transform(X_scaled)
gdf['PC1'] = components[:, 0]
gdf['PC2'] = components[:, 1]

# Visualizar componentes principales
fig, ax = plt.subplots(1, 1, figsize=(10, 8))
gdf.plot(column='PC1', cmap='viridis', legend=True, ax=ax)
plt.title("Componente Principal 1")
plt.show()
""")
]

# Agregar celdas al notebook
nb['cells'] = cells

# Guardar notebook
notebook_path = notebooks_dir / "01_exploratory_analysis.ipynb"
with open(notebook_path, "w", encoding="utf-8") as f:
    nbf.write(nb, f)

print(f"Notebook creado exitosamente en {notebook_path}")   
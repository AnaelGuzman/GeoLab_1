#!/usr/bin/env python3
"""
Script para procesar y cargar datos descargados en PostGIS.
"""

import geopandas as gpd
import os
import logging
from pathlib import Path
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Configuración de logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Cargar variables de entorno
load_dotenv()


class DataProcessor:
    def __init__(self):
        self.engine = self.create_db_connection()
        self.raw_dir = Path("data/raw")
        self.crs_target = "EPSG:32719"  # CRS para Chile
        self.ensure_schema_exists()

    def create_db_connection(self):
        db_url = (
            f"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}@"
            f"{os.getenv('POSTGRES_HOST', 'localhost')}:{os.getenv('POSTGRES_PORT', '5432')}/"
            f"{os.getenv('POSTGRES_DB')}"
        )
        return create_engine(db_url)

    def ensure_schema_exists(self):
        """Crea el esquema raw_data si no existe"""
        with self.engine.connect() as conn:
            conn.execute(text("CREATE SCHEMA IF NOT EXISTS raw_data;"))
        logger.info("✅ Esquema raw_data verificado/creado.")

    def load_to_postgis(self, gdf, table_name):
        try:
            gdf.to_postgis(table_name, self.engine, schema="raw_data", if_exists="replace", index=False)
            logger.info(f"✅ Tabla raw_data.{table_name} creada exitosamente.")
        except Exception as e:
            logger.error(f"❌ Error cargando {table_name}: {e}")

    def process_file(self, filename, table_name, extra_processing=None):
        file_path = self.raw_dir / filename
        if not file_path.exists():
            logger.warning(f"⚠️ Archivo {filename} no encontrado. Saltando...")
            return
        gdf = gpd.read_file(file_path)
        gdf = gdf.to_crs(self.crs_target)
        gdf = gdf[gdf.geometry.notnull()].copy()
        if extra_processing:
            extra_processing(gdf)
        self.load_to_postgis(gdf, table_name)

    def process_buildings(self):
        self.process_file("osm_buildings.geojson", "osm_buildings", extra_processing=lambda gdf: gdf.__setitem__("area", gdf.geometry.area))

    def process_amenities(self):
        self.process_file("osm_amenities.geojson", "osm_amenities")

    def process_boundaries(self):
        self.process_file("comuna_boundaries.geojson", "comuna_boundaries")

    def process_network(self):
        import osmnx as ox
        file_path = self.raw_dir / "osm_network.graphml"
        if not file_path.exists():
            logger.warning("⚠️ Archivo osm_network.graphml no encontrado. Saltando...")
            return
        G = ox.load_graphml(file_path)
        gdf_edges = ox.graph_to_gdfs(G, nodes=False, edges=True)
        gdf_edges = gdf_edges.to_crs(self.crs_target)
        gdf_edges = gdf_edges[gdf_edges.geometry.notnull()].copy()
        self.load_to_postgis(gdf_edges, "osm_network")

    def create_spatial_indices(self):
        logger.info("Creando índices espaciales...")
        tables = ["osm_buildings", "osm_amenities", "comuna_boundaries", "osm_network"]
        with self.engine.connect() as conn:
            for table in tables:
                try:
                    conn.execute(text(f"CREATE INDEX IF NOT EXISTS idx_{table}_geom ON raw_data.{table} USING GIST(geometry);"))
                    logger.info(f"Índice espacial creado para {table}")
                except Exception as e:
                    logger.error(f"Error creando índice en {table}: {e}")


def main():
    processor = DataProcessor()
    processor.process_buildings()
    processor.process_amenities()
    processor.process_boundaries()
    processor.process_network()
    processor.create_spatial_indices()
    logger.info("✅ Procesamiento completado.")


if __name__ == "__main__":
    main()
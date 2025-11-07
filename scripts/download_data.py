#!/usr/bin/env python3
"""
Script para descargar datos geoespaciales de la comuna definida en .env
"""

import os
import requests
import geopandas as gpd
import osmnx as ox
from pathlib import Path
from datetime import datetime
import logging
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()
COMUNA_NAME = os.getenv("COMUNA_NAME", "Peñaflor")

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DataDownloader:
    """Clase para gestionar la descarga de datos geoespaciales."""

    def __init__(self, comuna_name: str, output_dir: Path):
        self.comuna = comuna_name
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Inicializando descarga para comuna: {comuna_name}")

    def download_osm_data(self):
        """Descarga datos de OpenStreetMap usando OSMnx."""
        try:
            logger.info("Descargando red vial desde OSM...")
            place_query = f"{self.comuna}, Chile"

            # Red vial
            G = ox.graph_from_place(place_query, network_type='all')
            output_file = self.output_dir / 'osm_network.graphml'
            ox.save_graphml(G, output_file)
            logger.info(f"Red vial guardada en: {output_file}")

            # Edificios
            logger.info("Descargando edificios...")
            buildings = ox.features_from_place(place_query, tags={'building': True})
            buildings_file = self.output_dir / 'osm_buildings.geojson'
            buildings.to_file(buildings_file, driver='GeoJSON')
            logger.info(f"Edificios guardados en: {buildings_file}")

            # Amenidades
            logger.info("Descargando amenidades...")
            amenities = ox.features_from_place(place_query, tags={'amenity': True})
            amenities_file = self.output_dir / 'osm_amenities.geojson'
            amenities.to_file(amenities_file, driver='GeoJSON')
            logger.info(f"Amenidades guardadas en: {amenities_file}")

            return True

        except Exception as e:
            logger.error(f"Error descargando datos OSM: {e}")
            return False

    def download_boundaries(self):
        """Descarga límites administrativos de IDE Chile."""
        try:
            logger.info("Descargando límites administrativos...")
            wfs_url = "https://www.ide.cl/geoserver/wfs"
            params = {
                'service': 'WFS',
                'version': '2.0.0',
                'request': 'GetFeature',
                'typeName': 'division_comunal',
                'outputFormat': 'application/json',
                'CQL_FILTER': f"comuna ILIKE '{self.comuna}'"
            }
            response = requests.get(wfs_url, params=params)
            if response.status_code == 200:
                boundaries_file = self.output_dir / 'comuna_boundaries.geojson'
                with open(boundaries_file, 'w') as f:
                    f.write(response.text)
                logger.info(f"Límites guardados en: {boundaries_file}")
                return True
            else:
                logger.warning("No se pudieron descargar límites de IDE Chile")
                return False

        except Exception as e:
            logger.error(f"Error descargando límites: {e}")
            return False

    def create_metadata(self):
        """Crea archivo de metadatos de la descarga."""
        metadata = {
            'comuna': self.comuna,
            'fecha_descarga': datetime.now().isoformat(),
            'fuentes': ['OpenStreetMap', 'IDE Chile'],
            'archivos_generados': [str(p.name) for p in self.output_dir.glob('*')]
        }

        metadata_file = self.output_dir / 'metadata.txt'
        with open(metadata_file, 'w') as f:
            for key, value in metadata.items():
                f.write(f"{key}: {value}\n")

        logger.info(f"Metadatos guardados en: {metadata_file}")

# Ejecutar automáticamente
if __name__ == '__main__':
    output_path = Path("data/raw")  # ✅ Ruta corregida
    downloader = DataDownloader(COMUNA_NAME, output_path)
    downloader.download_osm_data()
    downloader.download_boundaries()
    downloader.create_metadata()
import os

class Config:
    # Základní konfigurace
    DEBUG = True
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'very_secret_key'

    # Přihlašovací údaje k databázi
    DB_NAME = 'DP_pokus'
    DB_USER = 'postgres'
    DB_PASSWORD = 'kapli4ky'
    DB_HOST = 'localhost'
    DB_PORT = '5432'

    # Připojení k ArcGIS API (pokud používáš nějaké přihlášení)
    ARCGIS_USERNAME = os.environ.get('ARCGIS_USERNAME') or 'your_username'
    ARCGIS_PASSWORD = os.environ.get('ARCGIS_PASSWORD') or 'your_password'

    # Další konfigurace může následovat zde

# Pokud potřebuješ použít více různých konfigurací (např. pro vývoj, testování, produkci),
# můžeš vytvořit různé třídy a dědit z Config, např. DevConfig(Config), ProdConfig(Config).

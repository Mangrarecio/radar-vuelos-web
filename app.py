import streamlit as st
import requests
import pandas as pd
import folium
from streamlit_folium import st_folium

# 1. CONFIGURACIÓN DE LA PÁGINA (Lo primero que lee el navegador)
st.set_page_config(page_title="Mi Radar de Vuelos", layout="wide")

st.title("✈️ Radar de Vuelos Profesional")
st.write("Esta aplicación muestra vuelos reales sobre España.")

# 2. FUNCIÓN PARA BUSCAR LOS AVIONES (El motor)
def descargar_datos():
    # Coordenadas de España (Lamin, Lomin, Lamax, Lomax)
    url = "https://opensky-network.org/api/states/all?lamin=34.0&lomin=-10.0&lamax=44.5&lomax=4.5"
    try:
        r = requests.get(url, timeout=10)
        datos = r.json()
        # Convertimos la lista de aviones en una tabla organizada
        columnas = ['icao24', 'callsign', 'pais', 'tiempo', 'contacto', 'long', 'lat', 'altitud', 'suelo', 'velocidad', 'rumbo']
        # Solo cogemos las primeras 11 columnas que nos da la API
        df = pd.DataFrame([fila[:11] for fila in datos['states']], columns=columnas)
        return df
    except:
        return None

# 3. DIBUJAR EL MAPA (La parte visual)
datos_aviones = descargar_datos()

if datos_aviones is not None:
    st.success(f"Se han detectado {len(datos_aviones)} aviones en el cielo.")
    
    # Crear un mapa centrado en Madrid
    m = folium.Map(location=[40.41, -3.70], zoom_start=6)

    # Poner cada avión en el mapa
    for _, avion in datos_aviones.iterrows():
        if avion['lat'] and avion['long']:
            folium.Marker(
                [avion['lat'], avion['long']],
                popup=f"Vuelo: {avion['callsign']}",
                icon=folium.Icon(color="blue", icon="plane")
            ).add_to(m)

    # Mostrar el mapa en la web
    st_folium(m, width=1000, height=600)
    
    # Mostrar la tabla debajo
    st.dataframe(datos_aviones[['callsign', 'pais', 'altitud', 'velocidad']])
else:
    st.error("Error al conectar con el satélite. Reintenta en unos segundos.")
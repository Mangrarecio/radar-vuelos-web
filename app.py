import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from opensky_api import OpenSkyApi # <--- La librería de tu enlace
import time

# --- CONFIGURACIÓN ---
USER_OPENSKY = "mangrarecio"
PASS_OPENSKY = "Manga1234@"

st.set_page_config(page_title="Radar Oficial OpenSky", layout="wide")

@st.cache_data(ttl=120)
def obtener_datos_con_libreria():
    # Inicializamos la API oficial
    api = OpenSkyApi(USER_OPENSKY, PASS_OPENSKY)
    
    try:
        # Pedimos los estados en el área de España
        # Parámetros: (lamin, lomin, lamax, lomax)
        s = api.get_states(bbox=(34.0, 44.5, -10.0, 4.5))
        
        if s is not None and s.states:
            # Convertimos los objetos de la librería a una lista para el DataFrame
            data = []
            for v in s.states:
                data.append([
                    v.icao24, v.callsign.strip(), v.origin_country, 
                    v.longitude, v.latitude, v.geo_altitude, 
                    v.velocity, v.true_track
                ])
            
            cols = ['icao24', 'callsign', 'pais', 'long', 'lat', 'altitud', 'velocidad', 'rumbo']
            return pd.DataFrame(data, columns=cols), "🟢 Conectado con API Oficial"
        
        return None, "⚠️ API en espera o sin vuelos"
    except Exception as e:
        if "429" in str(e):
            return None, "🔴 Error 429: Demasiadas peticiones (Espera)"
        return None, f"❌ Error: {str(e)}"

# --- INTERFAZ ---
st.title("🛰️ Radar Satelital - Biblioteca Oficial")

df, estado = obtener_datos_con_libreria()

st.sidebar.header("📊 Sistema")
st.sidebar.info(f"Estado: {estado}")

# Mapa de Google Satélite
m = folium.Map(location=[40.41, -3.70], zoom_start=6, 
               tiles='https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}',
               attr='Google Satellite')

if df is not None:
    for _, v in df.iterrows():
        if v['lat'] and v['long']:
            alt = int(v['altitud']) if v['altitud'] else 0
            rumb = int(v['rumbo']) if v['rumbo'] else 0
            color = "#FF0000" if alt < 1000 else "#FFFF00" if alt < 5000 else "#00FF00"
            
            folium.Marker(
                [v['lat'], v['long']],
                popup=f"Vuelo: {v['callsign']}",
                icon=folium.DivIcon(html=f'<div style="transform: rotate({rumb}deg); color: {color}; font-size: 22px; text-shadow: 2px 2px 3px #000;">✈</div>')
            ).add_to(m)
    st.success(f"Aviones detectados: {len(df)}")

st_folium(m, width="100%", height=600, key="mapa_oficial")
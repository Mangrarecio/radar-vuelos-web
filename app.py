import streamlit as st
import requests
import pandas as pd
import folium
from streamlit_folium import st_folium
from requests.auth import HTTPBasicAuth

# --- CONFIGURACIÓN ---
USER_OPENSKY = "mangrarecio"
PASS_OPENSKY = "Manga1234@"

st.set_page_config(page_title="Radar Satelital Profesional", layout="wide")

@st.cache_data(ttl=120)
def obtener_datos_estables():
    # Coordenadas rectificadas según la documentación oficial 1.4.0
    # bbox = (lamin, lamax, lomin, lomax)
    params = {
        'lamin': 34.0,
        'lamax': 44.5,
        'lomin': -10.0,
        'lomax': 4.5
    }
    
    url = "https://opensky-network.org/api/states/all"
    
    try:
        # Imitamos la cabecera de la librería oficial para evitar el rechazo
        headers = {'User-Agent': 'OpenSkyPythonAPI/1.4.0'}
        
        r = requests.get(
            url, 
            params=params, 
            auth=HTTPBasicAuth(USER_OPENSKY, PASS_OPENSKY),
            headers=headers,
            timeout=15
        )
        
        if r.status_code == 200:
            datos = r.json()
            if datos and 'states' in datos and datos['states']:
                # Mapeo de columnas según la documentación oficial
                cols = ['icao24', 'callsign', 'pais', 'tiempo', 'contacto', 'long', 'lat', 'altitud', 'suelo', 'velocidad', 'rumbo', 'v_vertical']
                df = pd.DataFrame([f[:12] for f in datos['states']], columns=cols)
                df['callsign'] = df['callsign'].str.strip()
                return df, "🟢 Conectado"
            return None, "⚠️ Área sin vuelos activos"
        elif r.status_code == 429:
            return None, "🔴 API Saturada (Límite 429)"
        elif r.status_code == 401:
            # Si las credenciales fallan, intentamos una vez como anónimo
            r_anon = requests.get(url, params=params, headers=headers, timeout=10)
            if r_anon.status_code == 200:
                return obtener_datos_estables.__wrapped__(None, None) # Recursión simple o manejo manual
            return None, "🚫 Credenciales/Acceso denegado"
        return None, f"Estado: {r.status_code}"
    except Exception as e:
        return None, f"Fallo de conexión: {str(e)}"

# --- INTERFAZ ---
st.title("🛰️ Radar de Vuelos - Vista Satélite")

df, status_msg = obtener_datos_estables()

st.sidebar.header("📊 Centro de Datos")
st.sidebar.write(f"**Usuario:** `{USER_OPENSKY}`")
st.sidebar.info(f"**Estado:** {status_msg}")

# Mapa de Google Satélite (Carga rápida)
m = folium.Map(
    location=[40.41, -3.70], 
    zoom_start=6, 
    tiles='https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}',
    attr='Google Satellite'
)

if df is not None:
    for _, v in df.iterrows():
        if v['lat'] and v['long']:
            alt = int(v['altitud']) if v['altitud'] else 0
            rumb = int(v['rumbo']) if v['rumbo'] else 0
            # Rojo: <1km, Amarillo: 1-5km, Verde: >5km
            color = "#FF0000" if alt < 1000 else "#FFFF00" if alt < 5000 else "#00FF00"
            
            folium.Marker(
                [v['lat'], v['long']],
                popup=f"Vuelo: {v['callsign']}<br>Alt: {alt}m",
                icon=folium.DivIcon(html=f'<div style="transform: rotate({rumb}deg); color: {color}; font-size: 22px; text-shadow: 2px 2px 3px #000;">✈</div>')
            ).add_to(m)
    st.success(f"Radar en línea: {len(df)} aeronaves.")
else:
    st.warning(f"Esperando datos: {status_msg}")

st_folium(m, width="100%", height=600, key="radar_v15_final")